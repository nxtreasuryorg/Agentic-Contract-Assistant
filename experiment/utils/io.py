import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple

import yaml


@dataclass
class RunPaths:
    base_dir: Path
    results_dir: Path
    run_dir: Path


def read_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(content)


def make_run_dirs(base_dir: Path, results_subdir: str = "results") -> RunPaths:
    results_dir = (base_dir / results_subdir).resolve()
    results_dir.mkdir(parents=True, exist_ok=True)
    run_id = time.strftime("%Y%m%d-%H%M%S")
    run_dir = results_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return RunPaths(base_dir=base_dir, results_dir=results_dir, run_dir=run_dir)


def build_rtf_paragraphs(lines: Tuple[str, ...]) -> str:
    # Minimal RTF with each line separated by \par
    safe_lines = []
    for ln in lines:
        ln = ln.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
        safe_lines.append(ln)
    body = "\\par\n".join(safe_lines)
    return "{\\rtf1\\ansi\n" + body + "\n}"


def ensure_absolute(base: Path, maybe_rel: str) -> Path:
    p = Path(maybe_rel)
    if not p.is_absolute():
        p = (base / p).resolve()
    return p
