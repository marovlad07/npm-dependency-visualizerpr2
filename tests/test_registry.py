"""Verify registry parsing and caching without an Internet connection."""

import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from npm_graph.errors import AppError
from npm_graph.registry import Package, Registry


class RegistryTests(unittest.TestCase):
    """Mock only HTTP transport; use the real parser and resolver."""

    def test_version_and_cache(self):
        """The requested version, rather than latest, controls dependencies."""
        data = {"versions": {
            "1.0.0": {"dependencies": {"old": "^1"}},
            "2.0.0": {"dependencies": {"new": "^2"}},
        }, "dist-tags": {"latest": "2.0.0"}}
        response = io.BytesIO(json.dumps(data).encode())
        with patch("npm_graph.registry.urlopen", return_value=response) as http:
            source = Registry("https://example.org")
            package = source.resolve("@scope/name", "1.0.0")
            self.assertEqual(source.dependencies(package), {"old": "^1"})
            self.assertEqual(http.call_count, 1)
            self.assertIn("@scope%2Fname", http.call_args[0][0].full_url)

    def test_http_and_invalid_json(self):
        """Network and malformed-response errors are understandable."""
        error = HTTPError("https://host", 404, "missing", {}, None)
        with patch("npm_graph.registry.urlopen", side_effect=error):
            with self.assertRaisesRegex(AppError, "HTTP 404"):
                Registry("https://host").resolve("missing", "1.0.0")
        with patch("npm_graph.registry.urlopen", return_value=io.BytesIO(b"!")):
            with self.assertRaises(AppError):
                Registry("https://host").resolve("bad", "1.0.0")

    def test_alias(self):
        """An npm alias identifies the underlying package."""
        source = Registry("https://host")
        source.cache["real"] = {"versions": {"1.0.0": {}}}
        self.assertEqual(source.resolve("alias", "npm:real@^1"),
                         Package("real", "1.0.0"))
