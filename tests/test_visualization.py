"""Check DOT topology and image-renderer failure handling."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from npm_graph.errors import AppError
from npm_graph.registry import Package
from npm_graph.visualization import dot_text, find_dot, render
from test_graph import fixture_graph


class VisualizationTests(unittest.TestCase):
    """Verify that visualization preserves cycles and isolated nodes."""

    def test_dot(self):
        """Every dependency edge survives DOT serialization."""
        root = Package("A", "1.0.0")
        cycle = dot_text(fixture_graph("cycle"), root)
        self.assertEqual(cycle.count(" -> "), 3)
        self.assertIn('"C@1.0.0" -> "A@1.0.0"', cycle)
        empty = dot_text(fixture_graph("empty"), root)
        self.assertIn('"A@1.0.0" [', empty)
        self.assertNotIn(" -> ", empty)

    def test_missing_renderer_and_bad_extension(self):
        """A missing renderer or unsupported image format fails clearly."""
        with self.assertRaises(AppError):
            find_dot("definitely-not-a-real-dot-executable")
        with self.assertRaisesRegex(AppError, "расширение"):
            render(fixture_graph("empty"), Package("A", "1.0.0"), "bad.jpg")

    def test_renderer_arguments(self):
        """Invoke dot as an argument list and write the DOT file first."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "graph.png"
            with patch("npm_graph.visualization.find_dot", return_value="dot"):
                with patch("npm_graph.visualization.subprocess.run") as process:
                    render(fixture_graph("cycle"),
                           Package("A", "1.0.0"), output)
            self.assertEqual(process.call_args[0][0][0:2], ["dot", "-Tpng"])
            self.assertEqual(output.with_suffix(".dot").read_text(
                encoding="utf-8"
            ).count(" -> "), 3)
