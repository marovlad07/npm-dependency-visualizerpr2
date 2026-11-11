# Справочник функций

Все функции используют стандартную библиотеку Python.
Документация также находится в docstring исходников.

## __init__.py


## __main__.py


## cli.py

- `parser` — Create the argument parser shared by all stages.
- `validate` — Check package, version and repository options before execution.
- `validate_url` — Require a valid HTTP(S) registry address without credentials.
- `execute` — Run the selected stage against a real or an offline repository.
- `output_graph` — Choose machine-readable output, DOT source or rendered image.
- `print_reverse` — Display dependents of a specific version rather than mixing versions.
- `print_direct` — Display exact root-version dependency declarations for stage two.
- `main` — Validate input and return a shell-compatible exit status.

## errors.py

- `AppError` — Describe invalid input or an unsuccessful external operation.

## graph.py

- `bfs` — Visit each reachable node once, preserving edges through neighbors.
- `build_graph` — Load dependencies lazily with BFS; cycles never enqueue twice.
- `graph_data` — Convert graph nodes and edges to a reproducible JSON structure.
- `reverse_dependencies` — Find direct and transitive dependents by BFS on reversed edges.
- `complete_test_graph` — Include all offline packages so disconnected dependents are visible.

## registry.py

- `Package` — Identify a node by both its package name and resolved version.
  - `label` — Return a human-readable, unambiguous graph label.
- `dependency_map` — Validate the dependency mapping returned by a metadata source.
- `Registry` — Download and cache packuments; never execute npm or package code.
  - `__init__` — Remember the base URL and initialize an in-memory cache.
  - `metadata` — Get all version metadata for one package with bounded I/O.
  - `resolve` — Resolve tags and ranges to a concrete published package.
  - `dependencies` — Return declared runtime dependencies of the exact version.

## semver.py

- `Version` — Compare semantic versions, ignoring build metadata.
  - `parse` — Parse a complete version and reject invalid identifiers.
  - `__lt__` — Apply SemVer ordering, including numeric prerelease parts.
- `prerelease_key` — Sort numeric identifiers before strings, then compare tuple prefixes.
- `partial` — Return a padded version and the count of specified components.
- `next_bound` — Return the exclusive upper bound for a partial version.
- `expand` — Expand one npm comparator into primitive comparisons.
- `wildcard_comparison` — An unbounded wildcard allows all stable versions except strict >/<.
- `compatible_range` — Compute caret or tilde bounds, including zero-major partials.
- `comparator_set` — Parse an AND group, including inclusive hyphen ranges.
- `compare` — Evaluate one comparison without dynamic code evaluation.
- `satisfies` — Accept a candidate only if an OR group and prerelease rule hold.
- `select_version` — Choose the highest matching published version or an explicit tag.

## test_repository.py

- `TestRepository` — Expose the same interface as the real npm registry.
  - `__init__` — Load and validate the whole fixture before traversing it.
  - `validate` — Check fixture names, exact versions and dependency declarations.
  - `resolve` — Select one available test version satisfying the requested range.
  - `dependencies` — Return runtime dependencies of a resolved fixture package.

## visualization.py

- `dot_text` — Serialize all nodes and edges, escaping labels as quoted strings.
- `find_dot` — Locate Graphviz in an explicit path, PATH or local tools folder.
- `render` — Save DOT and use Graphviz only to lay out the already-built graph.
- `open_image` — Display the result in the operating system's default viewer.
