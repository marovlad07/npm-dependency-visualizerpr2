"""Verify reverse traversal on diamonds, disconnected parents and cycles."""

import unittest

from npm_graph.graph import complete_test_graph, reverse_dependencies
from npm_graph.registry import Package
from npm_graph.test_repository import TestRepository
from test_graph import EXAMPLES, fixture_graph


class ReverseTests(unittest.TestCase):
    """Check the reversed relation and terminate on cyclic input."""

    def test_diamond(self):
        """Both branches are direct parents; the root is transitive."""
        graph = fixture_graph("diamond")
        direct, all_parents = reverse_dependencies(graph, Package("D", "1.0.0"))
        self.assertEqual([x.name for x in direct], ["B", "C"])
        self.assertEqual([x.name for x in all_parents], ["B", "C", "A"])

    def test_cycles_and_empty(self):
        """A package is excluded from its own dependent result."""
        for fixture, expected in [("cycle", ["C", "B"]),
                                  ("self", []), ("empty", [])]:
            _, parents = reverse_dependencies(
                fixture_graph(fixture), Package("A", "1.0.0")
            )
            self.assertEqual([x.name for x in parents], expected)

    def test_complete_repository(self):
        """Starting at a leaf still finds its offline parents."""
        source = TestRepository(EXAMPLES / "diamond.json")
        graph = complete_test_graph(source)
        self.assertIn(Package("Z", "1.0.0"), graph)
        direct, parents = reverse_dependencies(graph, Package("D", "1.0.0"))
        self.assertEqual(len(direct), 2)
        self.assertEqual(len(parents), 3)
