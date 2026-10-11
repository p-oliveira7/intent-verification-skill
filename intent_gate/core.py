"""Validate evidence contracts and evaluate intent without guessing semantics."""
import hashlib
import json

CATEGORIES = {
    "requirement_contradiction", "requirement_omission", "behavior_change",
    "document_conflict", "traceability_gap",
}
IMPACTS = {"critical": "P0", "high": "P1", "moderate": "P2", "low": "P3"}


class ContractError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ContractError(message)


def keys(obj, required, optional=()):
    require(isinstance(obj, dict), "Expected object")
    require(set(required) <= obj.keys(), f"Missing fields: {set(required) - obj.keys()}")
    require(obj.keys() <= set(required) | set(optional), "Unknown fields")


def nonempty(value, label):
    require(isinstance(value, str) and bool(value.strip()), f"Invalid {label}")


def enum(value, allowed, label):
    require(isinstance(value, str) and value in allowed, f"Invalid {label}")


def unique_index(items, label):
    require(isinstance(items, list), f"Expected list: {label}")
    result = {}
    for item in items:
        require(isinstance(item, dict), f"Invalid {label} entry")
        nonempty(item.get("id"), f"{label} id")
        require(item["id"] not in result, f"Duplicate {label} id")
        result[item["id"]] = item
    return result


def refs(value, index, label, allow_empty=False):
    require(isinstance(value, list), f"Expected reference list: {label}")
    require(allow_empty or len(value) > 0, f"Empty references: {label}")
    require(all(isinstance(x, str) for x in value), "Invalid reference")
    require(len(value) == len(set(value)), "Duplicate reference")
    require(all(x in index for x in value), f"Unknown reference: {label}")


def validate(bundle, analysis, policy):
    keys(policy, ["version", "blocking_severities", "mandatory_evidence_required"])
    nonempty(policy["version"], "policy version")
    require(isinstance(policy["blocking_severities"], list), "Invalid blocking severities")
    require(all(s in IMPACTS.values() for s in policy["blocking_severities"]), "Unknown severity")
    require(type(policy["mandatory_evidence_required"]) is bool, "Expected policy boolean")
    require("P0" in policy["blocking_severities"], "P0 must remain blocking in v1")

    keys(bundle, ["version", "base_commit", "head_commit", "evidence"])
    require(type(bundle["version"]) is int and bundle["version"] == 1, "Unsupported bundle version")
    for field in ["base_commit", "head_commit"]:
        require(isinstance(bundle[field], str) and len(bundle[field]) == 40
                and all(c in "0123456789abcdef" for c in bundle[field]), "Invalid commit")
    evidence = unique_index(bundle["evidence"], "evidence")
    for e in evidence.values():
        keys(e, ["id", "kind", "source", "text", "sha256"])
        enum(e["kind"], {"change_diff", "requirement_document"}, "evidence kind")
        nonempty(e["source"], "evidence source")
        require(isinstance(e["text"], str), "Invalid evidence text")
        require(hashlib.sha256(e["text"].encode()).hexdigest() == e["sha256"],
                "Evidence content hash mismatch")
    require(any(e["kind"] == "change_diff" for e in evidence.values()), "Missing diff evidence")

    keys(analysis, ["version", "head_commit", "scope_complete", "scope_reason",
                    "requirements", "candidates", "execution_dependencies"])
    require(type(analysis["version"]) is int and analysis["version"] == 1, "Unsupported analysis version")
    require(analysis["head_commit"] == bundle["head_commit"], "Analysis belongs to another change")
    require(type(analysis["scope_complete"]) is bool, "Expected scope boolean")
    nonempty(analysis["scope_reason"], "scope explanation")
    requirements = unique_index(analysis["requirements"], "requirement")
    candidates = unique_index(analysis["candidates"], "candidate")
    for r in requirements.values():
        keys(r, ["id", "mandatory", "status", "evidence_refs", "reason"])
        require(type(r["mandatory"]) is bool, "Expected mandatory boolean")
        enum(r["status"], {"satisfied", "violated", "unverified", "inconclusive", "not_applicable"}, "requirement status")
        nonempty(r["reason"], "requirement reason")
        refs(r["evidence_refs"], evidence, "requirement evidence")
        require(any(evidence[x]["kind"] == "requirement_document" for x in r["evidence_refs"]),
                "Requirement must reference a source document")
        if r["status"] == "satisfied":
            require(any(evidence[x]["kind"] == "change_diff" for x in r["evidence_refs"]),
                    "Satisfied requirement must reference the analyzed change")
    for c in candidates.values():
        keys(c, ["id", "category", "impact", "confidence", "assessment", "resolution",
                 "requirement_refs", "evidence_refs", "summary", "consequence", "reason",
                 "root_cause_key", "correction_key", "group_reason"])
        enum(c["category"], CATEGORIES, "category")
        enum(c["impact"], IMPACTS, "impact")
        enum(c["confidence"], {"high", "medium", "low"}, "confidence")
        enum(c["assessment"], {"supported", "uncertain", "text_only", "compensated"}, "assessment")
        # v1 deliberately has no waiver/acceptance protocol.
        enum(c["resolution"], {"open", "fixed"}, "resolution")
        for f in ["summary", "reason"]:
            nonempty(c[f], f)
        require(isinstance(c["consequence"], str), "Invalid consequence")
        if c["assessment"] in {"supported", "uncertain"}:
            nonempty(c["consequence"], "consequence")
        refs(c["requirement_refs"], requirements, "candidate requirements")
        refs(c["evidence_refs"], evidence, "candidate evidence")
        kinds = {evidence[x]["kind"] for x in c["evidence_refs"]}
        require({"change_diff", "requirement_document"} <= kinds,
                "Candidate must link requirement and change evidence")
        for f in ["root_cause_key", "correction_key", "group_reason"]:
            require(isinstance(c[f], str), f"Invalid {f}")
        if c["root_cause_key"] or c["correction_key"]:
            require(all(c[f].strip() for f in ["root_cause_key", "correction_key", "group_reason"]),
                    "Grouping requires cause, correction and justification")
    dependencies = unique_index(analysis["execution_dependencies"], "dependency")
    for d in dependencies.values():
        keys(d, ["id", "next_stage", "missing_information", "attempts", "why_indispensable", "question"])
        for f in ["next_stage", "missing_information", "why_indispensable", "question"]:
            nonempty(d[f], f)
        require(isinstance(d["attempts"], list) and len(d["attempts"]) > 0,
                "Dependency requires prior investigation")
        for attempt in d["attempts"]:
            nonempty(attempt, "investigation attempt")
    return evidence, requirements, candidates, dependencies


def evaluate(bundle, analysis, policy):
    _, requirements, candidates, dependencies = validate(bundle, analysis, policy)
    blockers, reviews, warnings, exclusions = [], [], [], []

    def reason(target, rule, ref, description):
        target.append({"rule": rule, "ref": ref, "reason": description})

    if not analysis["scope_complete"]:
        reason(reviews, "I-SCOPE", "scope", "Analysis scope is incomplete")
    for r in requirements.values():
        if r["status"] == "violated":
            reason(blockers if r["mandatory"] else warnings, "I-OBLIGATION", r["id"], r["reason"])
        elif r["status"] == "unverified":
            target = blockers if r["mandatory"] and policy["mandatory_evidence_required"] else reviews
            reason(target, "I-EVIDENCE", r["id"], r["reason"])
        elif r["status"] == "inconclusive":
            reason(reviews, "I-INCONCLUSIVE", r["id"], r["reason"])

    admitted = []
    for c in candidates.values():
        severity = IMPACTS[c["impact"]]
        if c["assessment"] in {"text_only", "compensated"}:
            exclusions.append({"id": c["id"], "rule": "I-EXCLUDE", "reason": c["reason"]})
            continue
        finding = dict(c, severity=severity)
        admitted.append(finding)
        if c["assessment"] == "uncertain":
            reason(reviews if severity in {"P0", "P1"} else warnings,
                   "I-UNCERTAINTY", c["id"], c["reason"])
            continue
        # Structured assessments can conflict: retain and surface the conflict.
        if c["category"] in {"requirement_contradiction", "requirement_omission"}:
            if any(requirements[x]["status"] in {"satisfied", "not_applicable"}
                   for x in c["requirement_refs"]):
                reason(reviews, "I-CONFLICT", c["id"], "Finding conflicts with obligation status")
        if c["resolution"] == "fixed":
            continue
        mandatory = any(requirements[x]["mandatory"] and requirements[x]["status"] != "not_applicable"
                        for x in c["requirement_refs"])
        violates = c["category"] in {"requirement_contradiction", "requirement_omission"}
        if severity == "P0" or (violates and (severity in policy["blocking_severities"] or mandatory)):
            reason(blockers, "I-VIOLATION", c["id"], c["consequence"])
        elif c["category"] in {"document_conflict", "traceability_gap"} and severity in {"P0", "P1"}:
            reason(reviews, "I-INTERPRETATION", c["id"], c["reason"])
        else:
            reason(warnings, "I-WARNING", c["id"], c["consequence"])
    for d in dependencies.values():
        reason(reviews, "I-DEPENDENCY", d["id"], d["why_indispensable"])

    grouped = {}
    for c in admitted:
        # Tuple keys avoid delimiter collisions. Stable member ordering is explicit.
        group_key = ("shared", c["root_cause_key"], c["correction_key"]) if c["root_cause_key"] else ("individual", c["id"], "")
        grouped.setdefault(group_key, []).append(c)
    groups = []
    for group_key, members in sorted(grouped.items()):
        members.sort(key=lambda c: c["id"])
        groups.append({"cause": group_key[1], "correction": group_key[2],
                       "severity": min(c["severity"] for c in members), "members": members})
    groups.sort(key=lambda g: (g["severity"], g["cause"], g["correction"]))
    for rows in [blockers, reviews, warnings, exclusions]:
        rows.sort(key=lambda row: (row.get("ref", row.get("id")), row["rule"]))
    decision = "BLOCK" if blockers else "REVIEW_REQUIRED" if reviews else "WARN" if warnings else "PASS"
    fingerprint = hashlib.sha256(json.dumps(
        {"bundle": bundle, "analysis": analysis, "policy": policy},
        sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode()).hexdigest()
    return {"version": 1, "decision": decision, "policy_version": policy["version"],
            "input_fingerprint": fingerprint, "head_commit": bundle["head_commit"],
            "can_continue": not bool(dependencies), "execution_dependencies": sorted(dependencies.values(), key=lambda d: d["id"]),
            "blockers": blockers, "reviews": reviews, "warnings": warnings,
            "exclusions": exclusions, "groups": groups,
            "obligations": sorted(requirements.values(), key=lambda r: r["id"]),
            "scope_complete": analysis["scope_complete"], "scope_reason": analysis["scope_reason"]}
