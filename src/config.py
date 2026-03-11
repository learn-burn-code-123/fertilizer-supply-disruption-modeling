"""Load and expose configuration from params.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load params.yaml from project root."""
    if config_path is None:
        config_path = Path(__file__).resolve().parent.parent / "params.yaml"
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with open(path) as f:
        return yaml.safe_load(f)


def get_project_root() -> Path:
    """Project root (parent of src/)."""
    return Path(__file__).resolve().parent.parent
