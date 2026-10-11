import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from intent_gate.collect import collect
from intent_gate.core import ContractError, evaluate

ROOT = Path(__file__).resolve().parents[1]


class TriageTests(unittest.TestCase):
    def setUp(self):
        self.bundle = json.loads((ROOT / "examples/bundle.json").read_text())
        self.analysis = json.loads((ROOT / "examples/analysis.json").read_text())
        self.policy = json.loads((ROOT / "policies/intent-v1.json").read_text())

    def run_gate(self):
        return evaluate(self.bundle, self.analysis, self.policy)

    def test_confirmed_mandatory_violation_blocks_without_execution_pause(self):
        result = self.run_gate()
        self.assertEqual(result["decision"], "BLOCK")
        self.assertTrue(result["can_continue"])
        self.assertEqual(result["groups"][0]["severity"], "P1")

    def test_missing_mandatory_evidence_blocks_even_without_candidates(self):
        self.analysis["candidates"] = []
        self.analysis["requirements"][0]["status"] = "unverified"
        self.assertEqual(self.run_gate()["decision"], "BLOCK")

    def test_critical_uncertainty_not_downgraded_by_confidence(self):
        c = self.analysis["candidates"][0]
        c.update(impact="critical", confidence="low", assessment="uncertain")
        self.analysis["requirements"][0]["status"] = "inconclusive"
        result = self.run_gate()
        self.assertEqual(result["decision"], "REVIEW_REQUIRED")
        self.assertEqual(result["groups"][0]["severity"], "P0")

    def test_text_only_exclusion_does_not_erase_mandatory_violation(self):
        self.analysis["candidates"][0]["assessment"] = "text_only"
        result = self.run_gate()
        self.assertEqual(result["decision"], "BLOCK")
        self.assertEqual(len(result["exclusions"]), 1)

    def test_valid_satisfied_requirement_and_text_difference_pass(self):
        self.analysis["requirements"][0]["status"] = "satisfied"
        self.analysis["candidates"][0]["assessment"] = "text_only"
        self.assertEqual(self.run_gate()["decision"], "PASS")

    def test_incomplete_scope_never_passes(self):
        self.analysis.update(requirements=[], candidates=[], scope_complete=False)
        self.assertEqual(self.run_gate()["decision"], "REVIEW_REQUIRED")

    def test_empty_complete_scope_requires_explanation(self):
        self.analysis.update(requirements=[], candidates=[], scope_reason="")
        with self.assertRaises(ContractError):
            self.run_gate()

    def test_nonmandatory_moderate_violation_warns(self):
        self.analysis["requirements"][0]["mandatory"] = False
        self.analysis["candidates"][0]["impact"] = "moderate"
        self.assertEqual(self.run_gate()["decision"], "WARN")

    def test_fixed_candidate_cannot_erase_open_obligation(self):
        self.analysis["candidates"][0]["resolution"] = "fixed"
        self.assertEqual(self.run_gate()["decision"], "BLOCK")

    def test_informal_waiver_is_rejected(self):
        self.analysis["candidates"][0]["resolution"] = "waived"
        with self.assertRaises(ContractError):
            self.run_gate()

    def test_unknown_evidence_is_rejected(self):
        self.analysis["candidates"][0]["evidence_refs"].append("MISSING")
        with self.assertRaises(ContractError):
            self.run_gate()

    def test_hash_mismatch_is_rejected(self):
        self.bundle["evidence"][0]["text"] += "edited"
        with self.assertRaises(ContractError):
            self.run_gate()

    def test_wrong_change_is_rejected(self):
        self.analysis["head_commit"] = "c" * 40
        with self.assertRaises(ContractError):
            self.run_gate()

    def test_boolean_is_not_a_version_number(self):
        self.bundle["version"] = True
        with self.assertRaises(ContractError):
            self.run_gate()

    def test_p0_open_behavior_change_cannot_be_informally_released(self):
        self.analysis["requirements"][0].update(status="satisfied", mandatory=False)
        self.analysis["candidates"][0].update(category="behavior_change", impact="critical")
        self.assertEqual(self.run_gate()["decision"], "BLOCK")

    def test_group_names_cannot_collide_with_individual_finding(self):
        first = self.analysis["candidates"][0]
        first.update(root_cause_key="", correction_key="", group_reason="")
        second = copy.deepcopy(first)
        second.update(id="INTENT-002", root_cause_key="candidate",
                      correction_key="INTENT-001", group_reason="Different demonstrated cause")
        self.analysis["candidates"].append(second)
        self.assertEqual(len(self.run_gate()["groups"]), 2)

    def test_duplicate_ids_and_unknown_fields_rejected(self):
        for mutate in [
            lambda a: a["candidates"].append(copy.deepcopy(a["candidates"][0])),
            lambda a: a.update(automatic_approval=True),
        ]:
            original = copy.deepcopy(self.analysis)
            mutate(self.analysis)
            with self.assertRaises(ContractError):
                self.run_gate()
            self.analysis = original

    def test_group_preserves_all_members_and_input_order_does_not_change_result(self):
        second = copy.deepcopy(self.analysis["candidates"][0])
        second.update(id="INTENT-002", impact="critical")
        self.analysis["candidates"].append(second)
        a = self.run_gate()
        self.analysis["candidates"].reverse()
        b = self.run_gate()
        self.assertEqual(a["groups"], b["groups"])
        self.assertEqual(a["blockers"], b["blockers"])
        self.assertEqual(len(a["groups"]), 1)
        self.assertEqual(len(a["groups"][0]["members"]), 2)
        self.assertEqual(a["groups"][0]["severity"], "P0")

    def test_grouping_requires_justification(self):
        self.analysis["candidates"][0]["group_reason"] = ""
        with self.assertRaises(ContractError):
            self.run_gate()

    def test_dependency_pauses_only_execution_and_preserves_approval_reasons(self):
        self.analysis["execution_dependencies"] = [{
            "id": "DEP-001", "next_stage": "security",
            "missing_information": "Applicable tenant boundary",
            "attempts": ["Read specification and ADR"],
            "why_indispensable": "Different boundaries change downstream authorization analysis",
            "question": "Which tenant boundary applies?",
        }]
        result = self.run_gate()
        self.assertEqual(result["decision"], "BLOCK")
        self.assertFalse(result["can_continue"])
        self.assertTrue(result["reviews"])

    def test_dependency_without_investigation_rejected(self):
        self.analysis["execution_dependencies"] = [{
            "id": "DEP-001", "next_stage": "security", "missing_information": "policy",
            "attempts": [], "why_indispensable": "needed", "question": "policy?",
        }]
        with self.assertRaises(ContractError):
            self.run_gate()

    def test_repeat_execution_is_identical(self):
        self.assertEqual(self.run_gate(), self.run_gate())

    def test_conflicting_satisfied_obligation_and_violation_retains_review(self):
        self.analysis["requirements"][0]["status"] = "satisfied"
        result = self.run_gate()
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("I-CONFLICT", [x["rule"] for x in result["reviews"]])

    def test_policy_cannot_remove_p0_blocking(self):
        self.policy["blocking_severities"] = ["P1"]
        with self.assertRaises(ContractError):
            self.run_gate()


class IntegrationTests(unittest.TestCase):
    def test_cli_example_and_invalid_input_exit_contract(self):
        command = [sys.executable, "-m", "intent_gate", "triage", "--bundle", "examples/bundle.json",
                   "--analysis", "examples/analysis.json", "--policy", "policies/intent-v1.json"]
        p = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout)["decision"], "BLOCK")
        with tempfile.TemporaryDirectory() as tmp:
            invalid = Path(tmp) / "invalid.json"
            invalid.write_text('{"version": 1, "version": 2}')
            command[command.index("examples/analysis.json")] = str(invalid)
            p = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(p.returncode, 2)
            self.assertEqual(p.stdout, "")

    def test_collector_reads_real_commits_without_modifying_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)

            def git(*args):
                return subprocess.check_output(["git", "-C", tmp, *args], stderr=subprocess.DEVNULL).decode().strip()

            git("init", "-b", "main")
            git("config", "user.name", "Fixture")
            git("config", "user.email", "fixture@example.invalid")
            (repo / "spec.md").write_text("Export requires permission.\n")
            (repo / "app.py").write_text("require_permission()\n")
            git("add", ".")
            git("commit", "-m", "baseline")
            base = git("rev-parse", "HEAD")
            (repo / "app.py").write_text("require_authenticated()\n")
            git("add", "app.py")
            git("commit", "-m", "change")
            (repo / "local.txt").write_text("preserve untracked file")
            before = git("status", "--porcelain")
            bundle = collect(repo, base, "HEAD", ["spec.md"])
            self.assertIn("+require_authenticated()", bundle["evidence"][0]["text"])
            self.assertEqual(bundle["evidence"][1]["text"], "Export requires permission.\n")
            for e in bundle["evidence"]:
                self.assertEqual(e["sha256"], hashlib.sha256(e["text"].encode()).hexdigest())
            self.assertEqual(before, git("status", "--porcelain"))
            self.assertEqual((repo / "local.txt").read_text(), "preserve untracked file")
            with self.assertRaises(ContractError):
                collect(repo, base, "HEAD", ["../secret.txt"])
            with self.assertRaises(ContractError):
                collect(repo, "--help", "HEAD", [])


if __name__ == "__main__":
    unittest.main()
