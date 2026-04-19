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

DEFAULT_EMPTY_COLUMNS = ["船号", "船名", "船长", "系统", "系统代号","主管长度"]
RESULT_COLUMNS = [
    "Prediction",
    "Error",
    "Relative_Error(%)",
    "y_predict",
    "abs_error",
    "rel_error_pct",
    "预测值",
    "绝对误差",
    "相对误差",
]
