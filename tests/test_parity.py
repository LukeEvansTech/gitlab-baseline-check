"""Both checkers must produce the same CSV, byte for byte, from the edge-case fixture.

Run with: python3 -m unittest discover -s tests
Set BASELINE_PS to the PowerShell to test (default pwsh; powershell for Windows PowerShell 5.1).
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE = os.path.join(ROOT, "tests", "fixtures", "edge-cases.json")
EXPECTED = os.path.join(ROOT, "tests", "fixtures", "edge-cases.expected.csv")


def read(path):
    """Return a file's bytes."""
    with open(path, "rb") as fh:
        return fh.read()


class Parity(unittest.TestCase):
    """Each checker must reproduce the expected CSV from the fixture."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)

    def test_python(self):
        """The Python checker reproduces the expected CSV."""
        out = os.path.join(self.tmp, "py.csv")
        proc = subprocess.run(
            [
                sys.executable,
                os.path.join(ROOT, "gitlab_baseline_check.py"),
                "--from-file",
                FIXTURE,
                "--csv",
                out,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertEqual(read(out), read(EXPECTED))
        self.assertNotIn("must-not-appear", proc.stdout)

    def test_powershell(self):
        """The PowerShell checker reproduces the expected CSV."""
        shell = os.environ.get("BASELINE_PS", "pwsh")
        if not shutil.which(shell):
            self.skipTest(shell + " not installed")
        out = os.path.join(self.tmp, "ps.csv")
        proc = subprocess.run(
            [
                shell,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                os.path.join(ROOT, "Test-GitLabBaseline.ps1"),
                "-FromFile",
                FIXTURE,
                "-CsvPath",
                out,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(read(out), read(EXPECTED))
        self.assertNotIn("must-not-appear", proc.stdout)


if __name__ == "__main__":
    unittest.main()
