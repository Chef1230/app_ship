from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from config.settings import DEFAULT_EMPTY_COLUMNS, RESULT_COLUMNS, SUPPORTED_IMPORT_SUFFIXES
from repositories.project_repository import ProjectRepository


class TableService:
    def __init__(self, project_repo: ProjectRepository | None = None) -> None:
        self.project_repo = project_repo or ProjectRepository()

    def empty_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(columns=DEFAULT_EMPTY_COLUMNS)

    def import_table(self, project_id: str, file_value: Any) -> pd.DataFrame:
        if not project_id:
            raise ValueError("请先选择或新建项目")

        file_path = self.validate_import_file(file_value)

        dataframe = self.project_repo.read_import_file(file_path)
        dataframe = self.clean_dataframe(dataframe)
        self.project_repo.save_current_table(project_id, dataframe)
        return dataframe

    def has_file(self, file_value: Any) -> bool:
        return file_value is not None

    def get_file_stem(self, file_value: Any) -> str:
        if hasattr(file_value, "orig_name") and file_value.orig_name:
            return Path(file_value.orig_name).stem.strip()

        file_path = self._extract_file_path(file_value)
        return file_path.stem.strip()

    def validate_import_file(self, file_value: Any) -> Path:
        file_path = self._extract_file_path(file_value)
        suffix = file_path.suffix.lower()
        if suffix not in SUPPORTED_IMPORT_SUFFIXES:
            raise ValueError("仅支持导入 CSV / Excel 文件")
        return file_path

    def clean_dataframe(self, value: Any) -> pd.DataFrame:
        dataframe = self.to_dataframe(value)
        if dataframe.empty and len(dataframe.columns) == 0:
            return self.empty_dataframe()

        dataframe = dataframe.copy()
        dataframe.columns = self._normalize_columns(dataframe.columns)
        dataframe = dataframe.replace(r"^\s*$", pd.NA, regex=True)
        dataframe = dataframe.dropna(axis=0, how="all").reset_index(drop=True)
        return dataframe

    def to_dataframe(self, value: Any) -> pd.DataFrame:
        if value is None:
            return self.empty_dataframe()

        if isinstance(value, pd.DataFrame):
            return value.copy()

        if isinstance(value, dict) and "data" in value:
            headers = value.get("headers")
            return pd.DataFrame(value["data"], columns=headers)

        return pd.DataFrame(value)

    def get_target_columns(self, value: Any) -> list[str]:
        dataframe = self.clean_dataframe(value)
        columns = [str(column) for column in dataframe.columns if str(column).strip()]
        target_columns = [column for column in columns if column not in RESULT_COLUMNS]
        return target_columns or columns

    def _normalize_columns(self, columns: pd.Index) -> list[str]:
        normalized: list[str] = []
        used: set[str] = set()
        for index, column in enumerate(columns, start=1):
            name = "" if column is None else str(column).strip()
            if not name or name.lower().startswith("unnamed"):
                name = f"column_{index}"

            base_name = name
            suffix = 2
            while name in used:
                name = f"{base_name}_{suffix}"
                suffix += 1

            normalized.append(name)
            used.add(name)

        return normalized

    def _extract_file_path(self, file_value: Any) -> Path:
        if file_value is None:
            raise ValueError("请先选择要导入的文件")

        if isinstance(file_value, (str, Path)):
            return Path(file_value)

        if hasattr(file_value, "path"):
            return Path(file_value.path)

        if hasattr(file_value, "name"):
            return Path(file_value.name)

        raise ValueError("无法识别上传文件路径")
