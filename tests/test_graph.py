"""Test graph topology, termination and offline repository validation."""

import json
import tempfile
import unittest
from pathlib import Path

from npm_graph.errors import AppError
from npm_graph.graph import bfs, build_graph
from npm_graph.registry import Package
from npm_graph.test_repository import TestRepository

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def fixture_graph(name):
    """Build the example rooted at A@1.0.0."""
    source = TestRepository(EXAMPLES / f"{name}.json")
    root = source.resolve("A", "1.0.0")
    return build_graph(source, root)


class GraphTests(unittest.TestCase):
    """Exercise cyclic, shared, empty and versioned dependency graphs."""

    def test_topologies(self):
        """Keep every edge and visit each reachable node only once."""
        for name, nodes, edges in [
            ("chain", 3, 2), ("diamond", 4, 4), ("cycle", 3, 3),
            ("empty", 1, 0), ("self", 1, 1), ("versions", 4, 3),
        ]:
            with self.subTest(name=name):
                graph = fixture_graph(name)
                self.assertEqual(len(graph), nodes)
                self.assertEqual(sum(map(len, graph.values())), edges)
        self.assertIn(Package("B", "1.2.0"), fixture_graph("versions"))
        self.assertIn(Package("B", "2.0.0"), fixture_graph("versions"))

    def test_breadth_first_and_deep_chain(self):
        """Traversal is BFS and does not use the Python call stack."""
        adjacency = {"A": ["B", "C"], "B": ["D"], "C": [], "D": []}
        self.assertEqual(bfs("A", adjacency.get), ["A", "B", "C", "D"])
        order = bfs(0, lambda node: [node + 1] if node < 1500 else [])
        self.assertEqual(len(order), 1501)
        with self.assertRaisesRegex(AppError, "лимит"):
            bfs(0, lambda node: [node + 1], limit=10)

    def test_invalid_repository(self):
        """Bad fixtures are rejected instead of silently losing edges."""
        cases = [[], {"packages": []}, {"packages": {"bad": {}}},
                 {"packages": {"A": {"1.0.0": {"dependencies": {
                     "MISSING": "1.0.0"
                 }}}}}]
        with tempfile.TemporaryDirectory() as directory:
            filename = Path(directory) / "bad.json"
            for data in cases:
                filename.write_text(json.dumps(data), encoding="utf-8")
                with self.subTest(data=data), self.assertRaises(AppError):
                    TestRepository(filename)
