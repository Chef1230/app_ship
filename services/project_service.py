from __future__ import annotations

from typing import Any

import pandas as pd

from config.settings import DEFAULT_PROJECT_NAME
from repositories.project_repository import ProjectRepository
from services.table_service import TableService


class ProjectService:
    def __init__(self, project_repo: ProjectRepository | None = None) -> None:
        self.project_repo = project_repo or ProjectRepository()
        self.table_service = TableService(self.project_repo)

    def create_project(
        self,
        project_name: str,
        vehicle_name: str = "",
        import_file: Any = None,
    ) -> dict:
        if self.table_service.has_file(import_file):
            self.table_service.validate_import_file(import_file)

        project_name = (project_name or "").strip() or DEFAULT_PROJECT_NAME
        if project_name == DEFAULT_PROJECT_NAME and self.table_service.has_file(import_file):
            project_name = self.table_service.get_file_stem(import_file) or DEFAULT_PROJECT_NAME

        vehicle_name = (vehicle_name or "").strip()
        meta = self.project_repo.create_project(project_name, vehicle_name)

        if self.table_service.has_file(import_file):
            self.table_service.import_table(meta["project_id"], import_file)

        return meta

    def list_projects(self) -> list[dict]:
        return self.project_repo.list_projects()

    def search_projects(self, keyword: str = "") -> list[dict]:
        keyword = (keyword or "").strip().lower()
        projects = self.list_projects()
        if not keyword:
            return projects

        return [
            project
            for project in projects
            if keyword in project.get("project_name", "").lower()
            or keyword in project.get("vehicle_name", "").lower()
        ]

    def get_project(self, project_id: str) -> dict:
        if not project_id:
            raise ValueError("请先选择项目")
        return self.project_repo.read_meta(project_id)

    def delete_project(self, project_id: str) -> None:
        if not project_id:
            raise ValueError("请先选择要删除的项目")
        self.project_repo.delete_project(project_id)

    def load_project_table(self, project_id: str) -> pd.DataFrame:
        if not project_id:
            raise ValueError("请先选择项目")
        return self.project_repo.load_current_table(project_id)

    def save_project_table(self, project_id: str, table_value: Any) -> pd.DataFrame:
        if not project_id:
            raise ValueError("请先选择或新建项目")

        dataframe = self.table_service.clean_dataframe(table_value)
        self.project_repo.save_current_table(project_id, dataframe)
        return dataframe

    def project_choices(self, keyword: str = "") -> list[tuple[str, str]]:
        return [
            (self.format_project_label(project), project["project_id"])
            for project in self.search_projects(keyword)
        ]

    @staticmethod
    def format_project_label(project: dict) -> str:
        name = project.get("project_name") or "未命名项目"
        vehicle = project.get("vehicle_name") or "未填写车辆"
        return f"{name} | {vehicle}"
