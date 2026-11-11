"""Construct dependency graphs by iterative breadth-first traversal."""

from collections import deque

from .errors import AppError

MAX_NODES = 5000


def bfs(start, neighbors, limit=MAX_NODES):
    """Visit each reachable node once, preserving edges through neighbors."""
    queue = deque([start])
    discovered = {start}
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for child in sorted(neighbors(node)):
            if child in discovered:
                continue
            if len(discovered) >= limit:
                raise AppError(f"Граф превышает лимит {limit} узлов")
            discovered.add(child)
            queue.append(child)
    return order


def build_graph(source, root):
    """Load dependencies lazily with BFS; cycles never enqueue twice."""
    adjacency = {}

    def load(package):
        """Resolve and store every outgoing edge before visiting children."""
        targets = {}
        for name, specification in sorted(source.dependencies(package).items()):
            try:
                child = source.resolve(name, specification)
            except AppError as error:
                raise AppError(f"{package.label} -> {name}: {error}") from error
            targets[child] = specification
        adjacency[package] = targets
        return targets

    bfs(root, load)
    return adjacency


def graph_data(graph, root):
    """Convert graph nodes and edges to a reproducible JSON structure."""
    return {
        "root": root.label,
        "nodes": [node.label for node in sorted(graph)],
        "edges": [
            {"from": parent.label, "to": child.label, "range": specification}
            for parent in sorted(graph)
            for child, specification in sorted(graph[parent].items())
        ],
    }


def reverse_dependencies(graph, target):
    """Find direct and transitive dependents by BFS on reversed edges."""
    if target not in graph:
        raise AppError(f"В построенном графе нет {target.label}")
    reversed_graph = {node: set() for node in graph}
    for parent, dependencies in graph.items():
        for child in dependencies:
            reversed_graph[child].add(parent)
    direct = sorted(reversed_graph[target] - {target})
    transitive = [node for node in bfs(target, reversed_graph.get)
                  if node != target]
    return direct, transitive


def complete_test_graph(source):
    """Include all offline packages so disconnected dependents are visible."""
    graph = {}
    for name, versions in source.packages.items():
        for version in versions:
            root = source.resolve(name, version)
            if root not in graph:
                graph.update(build_graph(source, root))
    return graph
