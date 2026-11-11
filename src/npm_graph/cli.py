"""Parse and validate the stage-one command-line configuration."""

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

from .errors import AppError
from .graph import (
    build_graph, complete_test_graph, graph_data, reverse_dependencies,
)
from .registry import Registry
from .semver import Version
from .test_repository import TestRepository

PACKAGE_PATTERN = r"(?:@[a-z0-9._-]+/)?[a-z0-9][a-z0-9._-]*"
TEST_PATTERN = r"[A-Z]+"


def parser():
    """Create the argument parser shared by all stages."""
    result = argparse.ArgumentParser(
        description="Визуализация зависимостей npm. ПР №2, вариант 14."
    )
    result.add_argument("--package", required=True, help="Имя пакета")
    result.add_argument("--version", required=True, help="Версия пакета")
    result.add_argument(
        "--repository", default="https://registry.npmjs.org",
        help="URL npm-реестра либо путь к тестовому JSON",
    )
    result.add_argument("--test", action="store_true", help="Тестовый JSON")
    result.add_argument(
        "--mode", choices=["config", "direct", "graph", "reverse"],
        default="graph",
    )
    result.add_argument(
        "--target", help="Узел имя@версия для обратных зависимостей"
    )
    return result


def validate(args):
    """Check package, version and repository options before execution."""
    pattern = TEST_PATTERN if args.test else PACKAGE_PATTERN
    if not re.fullmatch(pattern, args.package):
        raise AppError("Некорректное имя пакета для выбранного режима")
    if not args.version.strip() or any(c.isspace() for c in args.version):
        raise AppError("Версия должна быть непустой и без пробелов")
    Version.parse(args.version)
    if args.test:
        if not Path(args.repository).is_file():
            raise AppError("Не найден файл тестового репозитория")
        return
    url = urlsplit(args.repository)
    if url.scheme not in ("http", "https") or not url.hostname:
        raise AppError("Репозиторий должен быть HTTP(S) URL")
    if url.username or url.password or url.query or url.fragment:
        raise AppError("URL не должен содержать пароль, query или fragment")
    try:
        url.port
    except ValueError as error:
        raise AppError("Некорректный порт URL") from error


def execute(args):
    """Run the selected stage against a real or an offline repository."""
    if args.mode == "config":
        for key, value in vars(args).items():
            print(f"{key}={json.dumps(value, ensure_ascii=False)}")
        return
    source = TestRepository(args.repository) if args.test else Registry(
        args.repository
    )
    package = source.resolve(args.package, args.version)
    if args.mode == "direct":
        print_direct(source, package)
        return
    graph = build_graph(source, package)
    if args.mode == "reverse":
        if args.test:
            graph = complete_test_graph(source)
        print_reverse(graph, args.target or package.label)
        return
    print(json.dumps(graph_data(graph, package), ensure_ascii=False, indent=2))


def print_reverse(graph, label):
    """Display dependents of a specific version rather than mixing versions."""
    matches = [node for node in graph if node.label == label]
    if not matches:
        raise AppError(f"Нет узла {label!r}; нужен формат имя@версия")
    direct, transitive = reverse_dependencies(graph, matches[0])
    print(f"Обратные зависимости {label}:")
    print("Прямые: " + (", ".join(x.label for x in direct) or "нет"))
    print("Все (BFS): " + (", ".join(x.label for x in transitive) or "нет"))


def print_direct(source, package):
    """Display exact root-version dependency declarations for stage two."""
    dependencies = source.dependencies(package)
    print(f"Прямые зависимости {package.label}:")
    for name, specification in sorted(dependencies.items()):
        print(f"{name}: {specification}")
    if not dependencies:
        print("(нет зависимостей)")


def main(argv=None):
    """Validate input and return a shell-compatible exit status."""
    argument_parser = parser()
    args = argument_parser.parse_args(argv)
    try:
        validate(args)
        execute(args)
    except (AppError, OSError, ValueError) as error:
        argument_parser.exit(2, f"Ошибка: {error}\n")
    return 0
