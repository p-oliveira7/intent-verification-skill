"""End-to-end scenario: real Git collection and observed acceptance outcomes."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from intent_gate.core import evaluate

ROOT = Path(__file__).resolve().parents[1]


class CancellationDemoTests(unittest.TestCase):
    def test_documented_comparison_and_engine_replay(self):
        before = subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=ROOT)
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "comparison"
            proc = subprocess.run([sys.executable, "examples/cancellation/run_demo.py", "--out", str(out)],
                                  cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            summary = json.loads(proc.stdout)
            cases = {row["case"]: row for row in summary["cases"]}
            self.assertEqual([(cases[name]["passed"], cases[name]["failed"], cases[name]["decision"])
                              for name in ["correct", "refactor", "regression"]],
                             [(9, 0, "PASS"), (9, 0, "PASS"), (7, 2, "BLOCK")])
            self.assertEqual(cases["refactor"]["excluded"], 1)
            self.assertEqual(cases["regression"]["finding_groups"], 2)
            self.assertTrue(all(c["can_continue"] for c in cases.values()))
            self.assertTrue(summary["source_checkout_preserved"])
            for name in cases:
                folder = out / name
                bundle = json.loads((folder / "bundle.json").read_text())
                analysis = json.loads((folder / "analysis.json").read_text())
                policy = json.loads((ROOT / "policies/intent-v1.json").read_text())
                replay = evaluate(bundle, analysis, policy)
                self.assertEqual(replay, json.loads((folder / "intent-result.json").read_text()))
                self.assertIn("SHALL", bundle["evidence"][1]["text"])
                self.assertTrue((folder / "implementation.py").exists())
        self.assertEqual(before, subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=ROOT))


if __name__ == "__main__":
    unittest.main()
