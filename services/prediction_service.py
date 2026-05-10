from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import LeaveOneOut

from config.settings import RESULT_COLUMNS
from models.model_factory import ModelFactory
from repositories.project_repository import ProjectRepository
from services.table_service import TableService


class PredictionService:
    def __init__(self, project_repo: ProjectRepository | None = None) -> None:
        self.project_repo = project_repo or ProjectRepository()
        self.table_service = TableService(self.project_repo)

    def run_prediction(
        self,
        project_id: str,
        table_value: Any,
        model_name: str,
        target_col: str,
    ) -> tuple[pd.DataFrame, str]:
        if not project_id:
            raise ValueError("请先选择或新建项目")
        if not target_col:
            raise ValueError("请选择目标列")

        dataframe = self.table_service.clean_dataframe(table_value)
        if dataframe.empty:
            raise ValueError("当前表格为空，请先导入或填写数据")
        if target_col not in dataframe.columns:
            raise ValueError(f"目标列不存在：{target_col}")
        if len(dataframe) < 2:
            raise ValueError("Leave-One-Out 至少需要 2 行数据")

        base_df = self._drop_result_columns(dataframe)
        if target_col not in base_df.columns:
            raise ValueError(f"目标列不能是预测结果列：{target_col}")

        y = pd.to_numeric(base_df[target_col], errors="coerce")
        if y.isna().any():
            raise ValueError("当前最小版仅支持数值型目标列，请检查空值或文本值")

        feature_columns = [
            column
            for column in base_df.columns
            if column != target_col and column not in RESULT_COLUMNS
        ]
        X = base_df[feature_columns]

        predictions = np.zeros(len(base_df), dtype=float)
        loo = LeaveOneOut()
        for train_index, test_index in loo.split(base_df):
            predictor = ModelFactory.get_model(model_name)
            predictor.fit(X.iloc[train_index], y.iloc[train_index])
            predictions[test_index[0]] = float(predictor.predict(X.iloc[test_index])[0])

        result_df = base_df.copy()
        result_df["Prediction"] = predictions
        result_df["Error"] = y - result_df["Prediction"]
        result_df["Relative_Error(%)"] = (
            result_df["Error"].abs() / y.abs().replace(0, np.nan) * 100
        )

        metrics_markdown = self._format_metrics(y, predictions, result_df["Relative_Error(%)"])
        self.project_repo.save_latest_result(project_id, result_df)
        self.project_repo.save_current_table(project_id, result_df)
        return result_df, metrics_markdown

    def _drop_result_columns(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        existing_result_columns = [
            column for column in RESULT_COLUMNS if column in dataframe.columns
        ]
        if not existing_result_columns:
            return dataframe.copy()
        return dataframe.drop(columns=existing_result_columns).copy()

    def _format_metrics(
        self,
        y_true: pd.Series,
        y_predict: np.ndarray,
        rel_error_pct: pd.Series,
    ) -> str:
        mae = mean_absolute_error(y_true, y_predict)
        rmse = float(np.sqrt(mean_squared_error(y_true, y_predict)))
        mape = float(np.nanmean(rel_error_pct.to_numpy(dtype=float)))

        mape_text = "N/A" if np.isnan(mape) else f"{mape:.4f}%"
        return (
            f"平均绝对误差（MAE）：{mae:.4f}\n\n"
            f"平均相对误差（MAPE）：{mape_text}\n\n"
            f"均方根误差（RMSE）：{rmse:.4f}"
        )
