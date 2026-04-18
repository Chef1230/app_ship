from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PROJECTS_DIR = DATA_DIR / "projects"

APP_TITLE = "船舶管材预估系统"
DEFAULT_PROJECT_NAME = "未命名项目"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 7892

SUPPORTED_IMPORT_SUFFIXES = {".csv", ".xlsx", ".xls"}
SUPPORTED_IMPORT_SUFFIX = sorted(SUPPORTED_IMPORT_SUFFIXES)

DEFAULT_EMPTY_COLUMNS = ["车辆名称", "管材长度", "管材直径", "管材数量", "目标值"]
RESULT_COLUMNS = ["y_predict", "abs_error", "rel_error_pct"]
