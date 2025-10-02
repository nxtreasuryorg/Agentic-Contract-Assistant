from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, StrictUndefined


def _env_for(path: Path) -> Environment:
    # Jinja env rooted at project base (exp/)
    base = Path(__file__).resolve().parents[1]
    loader = FileSystemLoader(searchpath=base.as_posix())
    return Environment(loader=loader, autoescape=False, undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True)


def render_template(template_path: str, variables: Dict[str, Any]) -> str:
    base = Path(__file__).resolve().parents[1]
    env = _env_for(base)
    # Template path should be relative to exp/
    tmpl = env.get_template(template_path)
    return tmpl.render(**variables)


def pretty_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)
