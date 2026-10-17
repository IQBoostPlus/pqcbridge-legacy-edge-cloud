"""CLI safety regression: never allocate runtime state in the user's checkout."""
import subprocess
import sys
import json
import os
import tempfile
import unittest
from pathlib import Path


class BaselineCLIContract(unittest.TestCase):
    def test_runtime_inside_checkout_is_rejected_before_execution(self):
        repo = Path(__file__).resolve().parents[2]
        target = repo / "cloud_state" / "baseline-contract-must-not-exist"
        result = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("baseline.py")),
             "--runtime-root", str(target)], capture_output=True, text=True,
            timeout=10)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("runtime must be outside the repository", result.stderr)
        self.assertFalse(target.exists())

    @unittest.skipUnless(os.environ.get("BASELINE_RUN_INTEGRATION"),
                         "set BASELINE_RUN_INTEGRATION=1 for bounded full baseline")
    def test_isolated_baseline_reports_suite_and_received_readings_separately(self):
        configured_runtime = os.environ.get("BASELINE_CONTRACT_RUNTIME")
        runtime = (Path(configured_runtime) if configured_runtime else
                   Path(tempfile.mkdtemp(prefix="pqc-baseline-")) / "run")
        evidence = runtime.parent / (runtime.name + "-evidence")
        result = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("baseline.py")),
             "--runtime-root", str(runtime), "--evidence-dir", str(evidence)],
            capture_output=True, text=True, timeout=180)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        report = json.loads((evidence / "result.json").read_text())
        self.assertEqual(report["tests"]["status"], "passed")
        self.assertEqual(report["smoke"]["status"], "passed")
        self.assertGreaterEqual(report["smoke"]["cloud_reading_count"], 3)
        self.assertEqual(report["preservation"]["changed"], [])


if __name__ == "__main__":
    unittest.main()
