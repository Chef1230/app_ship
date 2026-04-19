from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from models.base_model import BasePredictor


class RPTPredictor(BasePredictor):
    """SAP RPT adapter for the app's BasePredictor interface."""

    _regressor_class: Any = None

    def __init__(self, max_context: int = 8192, bagging: int = 8) -> None:
        self.max_context = max_context
        self.bagging = bagging
        self.model_name = f"SAP_RPT_ctx{max_context}_b{bagging}"
        self.model: Any | None = None
        self.feature_columns: list[str] = []
        self._ensure_rpt_ready()

        self.model = self._regressor_class(
            max_context_size=max_context,
            bagging=bagging,
        )

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "RPTPredictor":
        X_prepared = self._prepare_features(X)
        y_prepared = pd.Series(y, index=X_prepared.index).astype(float)

        self.feature_columns = X_prepared.columns.tolist()
        self.model.fit(X_prepared, y_prepared)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if self.model is None:
            raise RuntimeError("SAP RPT 模型尚未初始化")

        X_prepared = self._prepare_features(X)
        X_prepared = self._align_features(X_prepared)

        # SAP RPT 在单样本预测时可能触发内部 np.concatenate 边界问题。
        if len(X_prepared) == 1:
            X_tmp = pd.concat([X_prepared, X_prepared], ignore_index=True)
            predictions = self.model.predict(X_tmp)
            return np.array([predictions[0]], dtype=float)

        return np.asarray(self.model.predict(X_prepared), dtype=float)

    def _prepare_features(self, X: pd.DataFrame) -> pd.DataFrame:
        if isinstance(X, pd.DataFrame):
            dataframe = X.copy()
        else:
            dataframe = pd.DataFrame(X)

        dataframe.columns = [str(column) for column in dataframe.columns]
        if dataframe.shape[1] == 0:
            dataframe["__dummy_feature"] = 0.0

        for column in dataframe.columns:
            series = dataframe[column]
            if pd.api.types.is_numeric_dtype(series):
                median = series.median()
                fill_value = 0.0 if pd.isna(median) else median
                dataframe[column] = series.fillna(fill_value)
            else:
                dataframe[column] = series.astype("string").fillna("missing")

        return dataframe

    def _align_features(self, X: pd.DataFrame) -> pd.DataFrame:
        if not self.feature_columns:
            return X

        aligned = X.copy()
        for column in self.feature_columns:
            if column not in aligned.columns:
                aligned[column] = "missing"

        return aligned[self.feature_columns]

    @classmethod
    def _ensure_rpt_ready(cls) -> None:
        if cls._regressor_class is not None:
            return

        try:
            from sap_rpt_oss import SAP_RPT_OSS_Regressor
        except ImportError as exc:
            raise RuntimeError(
                "未找到 sap_rpt_oss，请先确保 SAP RPT 模块所在目录已加入 Python 路径"
            ) from exc

        cls._regressor_class = SAP_RPT_OSS_Regressor


SAP_RPT_Adapter = RPTPredictor
