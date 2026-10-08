"""The checks page must match baseline.json.

Run with: python3 -m unittest discover -s tests
"""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import gen_checks_page  # noqa: E402  pylint: disable=wrong-import-position


class ChecksPage(unittest.TestCase):
    """docs/docs/checks.md is generated from baseline.json."""

    def test_page_is_current(self):
        """Regenerate with: python3 scripts/gen_checks_page.py"""
        with open(gen_checks_page.PAGE, encoding="utf-8") as fh:
            on_disk = fh.read().replace("\r\n", "\n")
        self.assertEqual(on_disk, gen_checks_page.render())


if __name__ == "__main__":
    unittest.main()
