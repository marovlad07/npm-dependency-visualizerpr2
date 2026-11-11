"""Read a small, versioned offline repository of uppercase package names."""

import json
import re
from pathlib import Path

from .errors import AppError
from .registry import Package, dependency_map
from .semver import Version, select_version


class TestRepository:
    """Expose the same interface as the real npm registry."""

    def __init__(self, filename):
        """Load and validate the whole fixture before traversing it."""
        try:
            data = json.loads(Path(filename).read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as error:
            raise AppError(f"Не удалось прочитать тестовый JSON: {error}")
        if not isinstance(data, dict) or not isinstance(
            data.get("packages"), dict
        ):
            raise AppError("В тестовом JSON нужен объект packages")
        self.packages = data["packages"]
        self.validate()

    def validate(self):
        """Check fixture names, exact versions and dependency declarations."""
        for name, versions in self.packages.items():
            if not re.fullmatch(r"[A-Z]+", name):
                raise AppError("Тестовые пакеты называются буквами A-Z")
            if not isinstance(versions, dict) or not versions:
                raise AppError(f"Не заданы версии пакета {name}")
            for version, manifest in versions.items():
                Version.parse(version)
                if not isinstance(manifest, dict):
                    raise AppError(f"Некорректный манифест {name}@{version}")
                dependencies = dependency_map(manifest.get("dependencies", {}))
                for dependency in dependencies:
                    if dependency not in self.packages:
                        raise AppError(f"В репозитории нет пакета {dependency}")

    def resolve(self, name, specification):
        """Select one available test version satisfying the requested range."""
        if name not in self.packages:
            raise AppError(f"В тестовом репозитории нет пакета {name}")
        version = select_version(self.packages[name], specification)
        return Package(name, version)

    def dependencies(self, package):
        """Return runtime dependencies of a resolved fixture package."""
        manifest = self.packages[package.name][package.version]
        return manifest.get("dependencies", {})
