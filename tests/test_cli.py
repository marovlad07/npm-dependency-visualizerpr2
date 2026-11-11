"""Check that invalid configuration is rejected before doing work."""

import contextlib
import io
import unittest

from npm_graph.cli import main


class CliTests(unittest.TestCase):
    """Exercise parameter validation through the actual CLI entry point."""

    def test_config(self):
        """The prototype prints the selected package and version."""
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            main(["--package", "is-odd", "--version", "3.0.1"])
        self.assertIn('package="is-odd"', output.getvalue())
        self.assertIn('version="3.0.1"', output.getvalue())

    def test_invalid_options(self):
        """Bad names, versions, URLs, modes and test files fail clearly."""
        base = ["--package", "is-odd", "--version", "3.0.1"]
        cases = [
            ["--package", "BAD!"], ["--version", ""],
            ["--repository", "not-a-url"], ["--mode", "unknown"],
            ["--test", "--package", "A", "--repository", "missing.json"],
            ["--test", "maybe"], ["--repository", "https://host:bad"],
        ]
        for extra in cases:
            with self.subTest(extra=extra):
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as caught:
                        main(base + extra)
                self.assertEqual(caught.exception.code, 2)
