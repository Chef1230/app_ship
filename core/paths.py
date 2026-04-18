from __future__ import annotations

from pathlib import Path

from config.settings import DATA_DIR, PROJECTS_DIR


def ensure_data_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)


def get_project_dir(project_id: str) -> Path:
    return PROJECTS_DIR / project_id
