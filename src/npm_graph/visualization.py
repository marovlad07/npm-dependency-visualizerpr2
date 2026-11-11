"""Write Graphviz DOT, render an image and open the system viewer."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from .errors import AppError

PROJECT = Path(__file__).resolve().parents[2]
RENDER_TIMEOUT = 45


def dot_text(graph, root):
    """Serialize all nodes and edges, escaping labels as quoted strings."""
    lines = [
        "digraph dependencies {",
        '  graph [rankdir=LR, bgcolor="#f8fafc", pad=0.4, nodesep=0.5,',
        '         dpi=144,',
        '         ranksep=0.9, fontname="Arial", fontsize=18,',
        f'         label={json.dumps(root.label)}, labelloc=t];',
        '  node [shape=box, style="rounded,filled", fontname="Arial",',
        '        fontsize=12, color="#cbd5e1", fillcolor="white",',
        '        margin=0.18];',
        '  edge [color="#64748b", fontname="Arial", fontsize=10];',
    ]
    for node in sorted(graph):
        color = ('fillcolor="#dbeafe", color="#2563eb"'
                 if node == root else '')
        lines.append(f"  {json.dumps(node.label)} [{color}];")
    for parent in sorted(graph):
        for child, specification in sorted(graph[parent].items()):
            lines.append(
                f"  {json.dumps(parent.label)} -> {json.dumps(child.label)} "
                f"[label={json.dumps(specification)}];"
            )
    lines.append("}")
    return "\n".join(lines) + "\n"


def find_dot(explicit=None):
    """Locate Graphviz in an explicit path, PATH or local tools folder."""
    explicit = explicit or os.environ.get("GRAPHVIZ_DOT")
    if explicit:
        candidate = shutil.which(explicit) or explicit
        if Path(candidate).is_file():
            return str(candidate)
        raise AppError(f"Не найден Graphviz: {explicit}")
    installed = shutil.which("dot")
    if installed:
        return installed
    local = sorted((PROJECT / ".tools").glob("graphviz/**/bin/dot.exe"))
    if local:
        return str(local[0])
    raise AppError(
        "Graphviz не найден. Установите его с graphviz.org/download/ "
        "и добавьте bin в PATH или передайте --dot путь/к/dot.exe"
    )


def render(graph, root, output, dot=None):
    """Save DOT and use Graphviz only to lay out the already-built graph."""
    output = Path(output)
    image_format = output.suffix.lstrip(".").lower()
    if image_format not in ("png", "svg"):
        raise AppError("Изображение должно иметь расширение .png или .svg")
    executable = find_dot(dot)
    output.parent.mkdir(parents=True, exist_ok=True)
    source = output.with_suffix(".dot")
    source.write_text(dot_text(graph, root), encoding="utf-8")
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    try:
        subprocess.run(
            [executable, f"-T{image_format}", str(source), "-o", str(output)],
            check=True, capture_output=True, timeout=RENDER_TIMEOUT,
            creationflags=flags,
        )
    except subprocess.CalledProcessError as error:
        detail = error.stderr.decode("utf-8", errors="replace")
        raise AppError(f"Graphviz не создал изображение: {detail}") from error
    except (OSError, subprocess.TimeoutExpired) as error:
        raise AppError(f"Ошибка запуска Graphviz: {error}") from error
    return output.resolve()


def open_image(path):
    """Display the result in the operating system's default viewer."""
    if os.name == "nt":
        os.startfile(str(path))
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])
