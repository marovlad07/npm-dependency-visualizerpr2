"""Fetch package metadata directly from an npm-compatible HTTP registry."""

import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from .errors import AppError
from .semver import select_version

TIMEOUT_SECONDS = 25
MAX_RESPONSE_BYTES = 50 * 1024 * 1024


@dataclass(frozen=True, order=True)
class Package:
    """Identify a node by both its package name and resolved version."""

    name: str
    version: str

    @property
    def label(self):
        """Return a human-readable, unambiguous graph label."""
        return f"{self.name}@{self.version}"


def dependency_map(value):
    """Validate the dependency mapping returned by a metadata source."""
    if not isinstance(value, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in value.items()
    ):
        raise AppError("dependencies должен быть объектом строка: строка")
    return value


class Registry:
    """Download and cache packuments; never execute npm or package code."""

    def __init__(self, url):
        """Remember the base URL and initialize an in-memory cache."""
        self.url = url.rstrip("/")
        self.cache = {}

    def metadata(self, name):
        """Get all version metadata for one package with bounded I/O."""
        if name in self.cache:
            return self.cache[name]
        url = f"{self.url}/{quote(name, safe='@')}"
        request = Request(url, headers={
            "Accept": "application/vnd.npm.install-v1+json",
            "User-Agent": "npm-graph-student/1.0",
        })
        try:
            with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise AppError(f"Слишком большой ответ реестра: {name}")
            data = json.loads(raw)
        except HTTPError as error:
            raise AppError(f"HTTP {error.code} для пакета {name}") from error
        except (URLError, TimeoutError, OSError, ValueError) as error:
            raise AppError(f"Ошибка получения {name}: {error}") from error
        if not isinstance(data, dict) or not isinstance(
            data.get("versions"), dict
        ):
            raise AppError(f"В ответе для {name} нет объекта versions")
        self.cache[name] = data
        return data

    def resolve(self, name, specification):
        """Resolve tags and ranges to a concrete published package."""
        if specification.startswith("npm:"):
            name, separator, specification = specification[4:].rpartition("@")
            if not separator or not name:
                raise AppError("Ожидался npm alias вида npm:имя@диапазон")
        data = self.metadata(name)
        version = select_version(
            data["versions"], specification, data.get("dist-tags")
        )
        return Package(name, version)

    def dependencies(self, package):
        """Return declared runtime dependencies of the exact version."""
        manifest = self.metadata(package.name)["versions"][package.version]
        if not isinstance(manifest, dict):
            raise AppError(f"Некорректный манифест {package.label}")
        return dependency_map(manifest.get("dependencies", {}))
