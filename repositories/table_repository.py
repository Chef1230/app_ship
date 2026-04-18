from pathlib import Path
import pandas as pd
from config.settings import DEFAULT_EMPTY_COLUMNS

class TableRepository:
    def current_table_path(self, project_dir: Path) -> Path:
        return project_dir / "tables" / "current.parquet"

    def original_table_path(self, project_dir: Path) -> Path:
        return project_dir / "tables" / "original.parquet"

    def save_current(self, project_dir: Path, df: pd.DataFrame):
        self.current_table_path(project_dir).parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(self.current_table_path(project_dir), index=False)

    def save_original(self, project_dir: Path, df: pd.DataFrame):
        self.original_table_path(project_dir).parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(self.original_table_path(project_dir), index=False)

    def load_current(self, project_dir: Path) -> pd.DataFrame:
        path = self.current_table_path(project_dir)
        if path.exists():
            return pd.read_parquet(path)
        return pd.DataFrame(columns=DEFAULT_EMPTY_COLUMNS)

    def init_empty_table(self, project_dir: Path):
        df = pd.DataFrame(columns=DEFAULT_EMPTY_COLUMNS)
        self.save_current(project_dir, df)
        self.save_original(project_dir, df)
        return df