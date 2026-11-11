"""Check npm range boundaries that affect graph correctness."""

import unittest

from npm_graph.errors import AppError
from npm_graph.semver import Version, select_version


class SemverTests(unittest.TestCase):
    """Cover stable versions, zero majors, prereleases and alternatives."""

    def test_ranges(self):
        """Select the highest version allowed by each npm range."""
        cases = [
            ("^1.2.3", ["1.2.3", "1.9.0", "2.0.0"], "1.9.0"),
            ("^0.2.3", ["0.2.3", "0.2.9", "0.3.0"], "0.2.9"),
            ("^0.0.3", ["0.0.3", "0.0.4"], "0.0.3"),
            ("^0.0", ["0.0.9", "0.1.0"], "0.0.9"),
            ("~1.2", ["1.2.9", "1.3.0"], "1.2.9"),
            ("1.x", ["1.9.9", "2.0.0"], "1.9.9"),
            ("1.2 - 2.3", ["2.3.9", "2.4.0"], "2.3.9"),
            (">= 1.0 < 2", ["1.8.0", "2.0.0"], "1.8.0"),
            ("<1 || >=2 <3", ["0.9.0", "1.0.0", "2.8.0"], "2.8.0"),
            (">1.2", ["1.2.9", "1.3.0"], "1.3.0"),
            ("<=1.2", ["1.2.9", "1.3.0"], "1.2.9"),
            ("*", ["1.0.0", "2.0.0-beta.1"], "1.0.0"),
            ("^1.2.3-beta.1", ["1.2.3-beta.2", "1.2.4-beta.1"],
             "1.2.3-beta.2"),
        ]
        for spec, versions, expected in cases:
            with self.subTest(spec=spec):
                self.assertEqual(select_version(versions, spec), expected)

    def test_tags_and_errors(self):
        """Tags resolve; unsupported references and empty matches fail."""
        self.assertEqual(select_version(["1.0.0"], "latest", {
            "latest": "1.0.0"
        }), "1.0.0")
        for spec in ["^9", "git+https://host/repo", "file:../local"]:
            with self.subTest(spec=spec), self.assertRaises(AppError):
                select_version(["1.0.0"], spec)

    def test_prerelease_order(self):
        """Numeric prerelease identifiers are compared numerically."""
        self.assertLess(Version.parse("1.0.0-beta.2"),
                        Version.parse("1.0.0-beta.10"))
        self.assertLess(Version.parse("1.0.0-rc.1"), Version.parse("1.0.0"))
        self.assertEqual(Version.parse("1.0.0+build"), Version.parse("1.0.0"))
