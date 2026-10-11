"""Reproduce a documented synthetic comparison; not an autonomous LLM evaluator."""
import argparse
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SCENARIO = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from intent_gate.collect import collect
from intent_gate.core import evaluate

TEST_RUNNER = '''
import io,json,sys,unittest
suite=unittest.defaultTestLoader.discover(sys.argv[1])
result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=2).run(suite)
print(json.dumps({"count":result.testsRun,"failures":[{"test":t.id(),"detail":s} for t,s in result.failures],"errors":[{"test":t.id(),"detail":s} for t,s in result.errors],"skipped":[{"test":t.id(),"reason":s} for t,s in result.skipped]}))
sys.exit(0 if result.wasSuccessful() else 1)
'''


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], stderr=subprocess.PIPE).decode().strip()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def prepare_analysis(bundle, profile, reference):
    document_refs = [e["id"] for e in bundle["evidence"] if e["kind"] == "requirement_document"]
    evidence_refs = ["DIFF-001", *document_refs]
    requirements = [{
        "id": id_, "mandatory": True,
        "status": "violated" if id_ in profile["violated"] else "satisfied",
        "evidence_refs": evidence_refs,
        "reason": "Interpretação registrada: " + (
            "a mudança contradiz este requisito; ver candidato e observações dos testes."
            if id_ in profile["violated"] else
            "a implementação mantém este requisito; código completo foi inspecionado e os casos correspondentes foram executados."
        ),
    } for id_ in reference["requirements"]]
    candidates = copy.deepcopy(profile["candidates"])
    for candidate in candidates:
        candidate["evidence_refs"] = evidence_refs
    return {
        "version": 1, "head_commit": bundle["head_commit"], "scope_complete": True,
        "scope_reason": "Escopo sintético: seis requisitos de cancelamento, documentos e código completos analisados pelo agente; este arquivo reproduz a interpretação registrada, não nova inferência.",
        "requirements": requirements, "candidates": candidates, "execution_dependencies": [],
    }


def run(output):
    output = Path(output)
    # Preserve existing user files rather than overwrite a previous run.
    output.mkdir(parents=True, exist_ok=False)
    reference = json.loads((SCENARIO / "analysis-reference.json").read_text())
    policy = json.loads((ROOT / "policies/intent-v1.json").read_text())
    expected_failures = {"test_cancel_day_zero_full_refund", "test_cancel_day_seven_full_refund"}
    records = []
    before = git(ROOT, "status", "--porcelain=v1")
    with tempfile.TemporaryDirectory(prefix="intent-cancellation-git-") as scratch:
        repo = Path(scratch)
        shutil.copytree(SCENARIO / "project", repo, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "validation.md"))
        git(repo, "init", "-b", "main")
        git(repo, "config", "user.name", "Synthetic Fixture")
        git(repo, "config", "user.email", "fixture@example.invalid")
        # Avoid executing hooks or inheriting signing requirements in the fixture.
        git(repo, "config", "core.hooksPath", str(repo / "no-hooks"))
        git(repo, "config", "commit.gpgsign", "false")
        (repo / "cancellation.py").write_text("# Feature not implemented yet.\n")
        git(repo, "add", ".")
        git(repo, "commit", "-m", "docs: define synthetic cancellation requirements")
        empty_base = git(repo, "rev-parse", "HEAD")
        correct_base = None
        for case in ["correct", "refactor", "regression"]:
            if case != "correct":
                git(repo, "checkout", "-B", f"case-{case}", correct_base)
            source = SCENARIO / ("project/cancellation.py" if case == "correct" else f"variants/{case}.py")
            shutil.copyfile(source, repo / "cancellation.py")
            git(repo, "add", "cancellation.py")
            git(repo, "commit", "-m", f"test: exercise {case} scenario")
            head = git(repo, "rev-parse", "HEAD")
            if case == "correct":
                correct_base = head
            bundle = collect(repo, empty_base if case == "correct" else correct_base, head,
                             ["docs/PRD.md", "docs/TDD.md", ".specs/features/order-cancellation/spec.md"])
            env = os.environ.copy()
            env["CANCELLATION_MODULE"] = str(repo / "cancellation.py")
            proc = subprocess.run([sys.executable, "-c", TEST_RUNNER, str(repo / "tests")],
                                  env=env, capture_output=True, text=True)
            if proc.returncode not in {0, 1}:
                raise RuntimeError(f"Runner did not complete: {case}")
            try:
                observed = json.loads(proc.stdout)
            except ValueError as exc:
                raise RuntimeError(f"No valid runner result: {case}") from exc
            names = {row["test"].split(".")[-1] for row in observed["failures"]}
            wanted = expected_failures if case == "regression" else set()
            if (observed["count"] != 9 or observed["errors"] or observed["skipped"]
                    or names != wanted or len(observed["failures"]) != len(wanted)
                    or proc.returncode != (1 if wanted else 0)):
                raise RuntimeError(f"Acceptance outcomes differ from documented expectations: {case}")
            analysis = prepare_analysis(bundle, reference["cases"][case], reference)
            result = evaluate(bundle, analysis, policy)
            expected_decision = "BLOCK" if case == "regression" else "PASS"
            if result["decision"] != expected_decision or not result["can_continue"]:
                raise RuntimeError(f"Unexpected Intent decision: {case}")
            folder = output / case
            folder.mkdir()
            save(folder / "bundle.json", bundle)
            save(folder / "analysis.json", analysis)
            save(folder / "test-results.json", dict(observed, exit_code=proc.returncode))
            save(folder / "intent-result.json", result)
            shutil.copyfile(source, folder / "implementation.py")
            records.append({"case": case, "tests": observed["count"],
                            "passed": observed["count"] - len(observed["failures"]),
                            "failed": len(observed["failures"]), "runner_errors": 0,
                            "decision": result["decision"], "can_continue": result["can_continue"],
                            "finding_groups": len(result["groups"]), "excluded": len(result["exclusions"]),
                            "head_commit": head})
    if git(ROOT, "status", "--porcelain=v1") != before:
        raise RuntimeError("Source checkout changed during comparison")
    summary = {"version": 1, "mode": "recorded-semantic-analysis-replay",
               "cases": records, "source_checkout_preserved": True}
    save(output / "summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="New output directory outside source checkout")
    args = parser.parse_args()
    output = Path(args.out).resolve()
    if output == ROOT or ROOT in output.parents:
        parser.error("Use an output directory outside the source checkout")
    try:
        print(json.dumps(run(output), ensure_ascii=False, indent=2))
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"Comparison failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
