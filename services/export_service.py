from __future__ import annotations

from typing import Any

from repositories.project_repository import ProjectRepository
from services.table_service import TableService


class ExportService:
    def __init__(self, project_repo: ProjectRepository | None = None) -> None:
        self.project_repo = project_repo or ProjectRepository()
        self.table_service = TableService(self.project_repo)

    def export_excel(self, project_id: str, table_value: Any) -> str:
        if not project_id:
            raise ValueError("请先选择或新建项目")

        dataframe = self.table_service.clean_dataframe(table_value)
        export_path = self.project_repo.export_excel(project_id, dataframe)
        return str(export_path)
