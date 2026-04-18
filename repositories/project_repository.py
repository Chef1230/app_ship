from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd

from config.settings import DEFAULT_EMPTY_COLUMNS, PROJECTS_DIR


class ProjectRepository:
    def __init__(self, projects_dir: Path | None = None) -> None:
        self.projects_dir = Path(projects_dir or PROJECTS_DIR)
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def list_projects(self) -> list[dict]:
        projects: list[dict] = []
        for project_dir in self.projects_dir.iterdir():
            if not project_dir.is_dir():
                continue

            meta_path = project_dir / "meta.json"
            if not meta_path.exists():
                continue

            projects.append(self.read_meta(project_dir.name))

        projects.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
        return projects

    def create_project(self, project_name: str, vehicle_name: str = "") -> dict:
        project_id = f"project_{uuid.uuid4().hex[:8]}"
        project_dir = self.get_project_dir(project_id)
        project_dir.mkdir(parents=True, exist_ok=False)

        now = self._now()
        meta = {
            "project_id": project_id,
            "project_name": project_name,
            "vehicle_name": vehicle_name,
            "created_at": now,
            "updated_at": now,
        }
        self.write_meta(project_id, meta)
        self.save_current_table(project_id, pd.DataFrame(columns=DEFAULT_EMPTY_COLUMNS))
        return meta

    def read_meta(self, project_id: str) -> dict:
        meta_path = self.get_project_dir(project_id) / "meta.json"
        with meta_path.open("r", encoding="utf-8") as file:
            meta = json.load(file)

        meta.setdefault("project_id", project_id)
        meta.setdefault("project_name", "未命名项目")
        meta.setdefault("vehicle_name", "")
        meta.setdefault("created_at", "")
        meta.setdefault("updated_at", meta.get("created_at", ""))
        return meta

    def write_meta(self, project_id: str, meta: dict) -> None:
        project_dir = self.get_project_dir(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)
        with (project_dir / "meta.json").open("w", encoding="utf-8") as file:
            json.dump(meta, file, ensure_ascii=False, indent=2)

    def update_project_meta(self, project_id: str, **updates: str) -> dict:
        meta = self.read_meta(project_id)
        meta.update(updates)
        meta["updated_at"] = self._now()
        self.write_meta(project_id, meta)
        return meta

    def delete_project(self, project_id: str) -> None:
        project_dir = self.get_project_dir(project_id).resolve()
        projects_dir = self.projects_dir.resolve()

        try:
            is_inside_projects = project_dir.is_relative_to(projects_dir)
        except AttributeError:
            is_inside_projects = str(project_dir).startswith(str(projects_dir))

        if not is_inside_projects or project_dir == projects_dir:
            raise ValueError("项目路径不安全，已取消删除")

        if project_dir.exists():
            shutil.rmtree(project_dir)

    def load_current_table(self, project_id: str) -> pd.DataFrame:
        path = self.current_table_path(project_id)
        if not path.exists():
            path = self._legacy_current_table_path(project_id)

        if path.exists():
            return pd.read_parquet(path)

        return pd.DataFrame(columns=DEFAULT_EMPTY_COLUMNS)

    def save_current_table(self, project_id: str, dataframe: pd.DataFrame) -> None:
        dataframe = self._prepare_table_for_storage(dataframe)
        path = self.current_table_path(project_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        dataframe.to_parquet(path, index=False)
        self.touch_project(project_id)

    def save_latest_result(self, project_id: str, dataframe: pd.DataFrame) -> None:
        dataframe = self._prepare_table_for_storage(dataframe)
        path = self.latest_result_path(project_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        dataframe.to_parquet(path, index=False)
        self.touch_project(project_id)

    def export_excel(self, project_id: str, dataframe: pd.DataFrame) -> Path:
        path = self.export_path(project_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        dataframe.to_excel(path, index=False)
        self.touch_project(project_id)
        return path

    def read_import_file(self, file_path: str | Path) -> pd.DataFrame:
        path = Path(file_path)
        suffix = path.suffix.lower()
        if suffix == ".csv":
            try:
                return pd.read_csv(path, encoding="utf-8-sig")
            except UnicodeDecodeError:
                return pd.read_csv(path, encoding="gbk")

        if suffix in {".xlsx", ".xls"}:
            return pd.read_excel(path)

        raise ValueError("仅支持导入 CSV / Excel 文件")

    def touch_project(self, project_id: str) -> None:
        meta_path = self.get_project_dir(project_id) / "meta.json"
        if not meta_path.exists():
            return
        meta = self.read_meta(project_id)
        meta["updated_at"] = self._now()
        self.write_meta(project_id, meta)

    def get_project_dir(self, project_id: str) -> Path:
        return self.projects_dir / project_id

    def current_table_path(self, project_id: str) -> Path:
        return self.get_project_dir(project_id) / "current.parquet"

    def latest_result_path(self, project_id: str) -> Path:
        return self.get_project_dir(project_id) / "latest_result.parquet"

    def export_path(self, project_id: str) -> Path:
        return self.get_project_dir(project_id) / "export.xlsx"

    def _legacy_current_table_path(self, project_id: str) -> Path:
        return self.get_project_dir(project_id) / "tables" / "current.parquet"

    def _prepare_table_for_storage(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        prepared = dataframe.copy()
        prepared.columns = [str(column) for column in prepared.columns]

        for column in prepared.columns:
            series = prepared[column]
            if not (
                pd.api.types.is_object_dtype(series)
                or pd.api.types.is_string_dtype(series)
            ):
                continue

            text_series = series.astype("string")
            non_empty = series.notna() & text_series.str.strip().ne("")
            numeric_series = pd.to_numeric(series, errors="coerce")

            if non_empty.any() and numeric_series[non_empty].notna().all():
                prepared[column] = numeric_series
            else:
                prepared[column] = text_series

        return prepared

    @staticmethod
    def _now() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
