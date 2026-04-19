from __future__ import annotations

import sys
from typing import Any

import numpy as np
import pandas as pd

from models.base_model import BasePredictor

# ------------- 配置区域 -------------
# 添加 TabPFN 本地路径到 sys.path；用户按本地环境自行配置该路径。
TABPFN_PATH = "/data1/chef/TabPFN_local/TabPFN/src"
# ---------------------------------


class TabPFNPredictor(BasePredictor):
    """
    使用本地 TabPFN 模型进行回归预测。

    支持 v2 和 v2.5 版本的模型权重，并适配当前系统使用的
    BasePredictor.fit(X, y) / predict(X) 接口。
    """

    V2_5_MODELS = {
        "default": "tabpfn-v2.5-regressor-v2.5_default.ckpt",
        "low-skew": "tabpfn-v2.5-regressor-v2.5_low-skew.ckpt",
        "quantiles": "tabpfn-v2.5-regressor-v2.5_quantiles.ckpt",
        "real-variant": "tabpfn-v2.5-regressor-v2.5_real-variant.ckpt",
        "real": "tabpfn-v2.5-regressor-v2.5_real.ckpt",
        "small-samples": "tabpfn-v2.5-regressor-v2.5_small-samples.ckpt",
        "variant": "tabpfn-v2.5-regressor-v2.5_variant.ckpt",
    }

    _tabpfn_regressor_class: Any = None
    _model_version_class: Any = None

    def __init__(
        self,
        version: str = "v2.5",
        model_name: str = "default",
        **model_kwargs: Any,
    ) -> None:
        self.version = version
        self.model_name = model_name
        self.model_kwargs = model_kwargs
        self.model: Any | None = None
        self.feature_columns: list[str] = []

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "TabPFNPredictor":
        self._ensure_tabpfn_ready()
        X_prepared = self._prepare_features(X)
        y_prepared = pd.Series(y, index=X_prepared.index).astype(float)

        self.feature_columns = X_prepared.columns.tolist()
        self.model = self._create_model()
        self._print_model_load_info(self.model)
        self.model.fit(X_prepared, y_prepared)
        print("[TabPFN] 模型训练完成")
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if self.model is None:
            raise RuntimeError("Model is not trained yet. Call fit() first.")

        X_prepared = self._prepare_features(X)
        X_prepared = self._align_features(X_prepared)
        return np.asarray(self.model.predict(X_prepared), dtype=float)

    def get_model_info(self) -> dict[str, Any]:
        info: dict[str, Any] = {
            "version": self.version,
            "model_name": self.model_name,
        }
        if self.model is not None:
            if hasattr(self.model, "models_"):
                info["num_models"] = len(self.model.models_)
            if hasattr(self.model, "configs_"):
                info["config_keys"] = [
                    list(config.__dict__.keys()) for config in self.model.configs_
                ]
        return info

    def _create_model(self) -> Any:
        if self.version == "v2.5":
            model_version = self._model_version_class.V2_5
            print(f"[TabPFN] 正在加载 v2.5 版本模型 (model_name={self.model_name})...")
            return self._tabpfn_regressor_class.create_default_for_version(
                model_version,
                **self.model_kwargs,
            )

        if self.version == "v2":
            model_version = self._model_version_class.V2
            print("[TabPFN] 正在加载 v2 版本模型...")
            return self._tabpfn_regressor_class.create_default_for_version(
                model_version,
                **self.model_kwargs,
            )

        print(f"[TabPFN] 使用自定义模型路径: {self.model_kwargs.get('model_path', 'auto')}")
        return self._tabpfn_regressor_class(**self.model_kwargs)

    def _prepare_features(self, X: pd.DataFrame) -> pd.DataFrame:
        if isinstance(X, pd.DataFrame):
            dataframe = X.copy()
        else:
            dataframe = pd.DataFrame(X)

        dataframe.columns = [str(column) for column in dataframe.columns]
        if dataframe.shape[1] == 0:
            dataframe["__dummy_feature"] = 0.0

        for column in dataframe.select_dtypes(include=["object", "string"]).columns:
            dataframe[column] = dataframe[column].astype("category")

        return dataframe

    def _align_features(self, X: pd.DataFrame) -> pd.DataFrame:
        if not self.feature_columns:
            return X

        aligned = X.copy()
        for column in self.feature_columns:
            if column not in aligned.columns:
                aligned[column] = pd.NA

        return aligned[self.feature_columns]

    def _print_model_load_info(self, model: Any) -> None:
        if hasattr(model, "models_") and model.models_:
            for index, model_item in enumerate(model.models_):
                print(f"[TabPFN] 模型 {index} 类型: {type(model_item).__name__}")
        if hasattr(model, "configs_") and model.configs_:
            print(f"[TabPFN] 配置数量: {len(model.configs_)}")

    @classmethod
    def _ensure_tabpfn_ready(cls) -> None:
        if cls._tabpfn_regressor_class is not None and cls._model_version_class is not None:
            return

        if TABPFN_PATH and TABPFN_PATH not in sys.path:
            sys.path.insert(0, TABPFN_PATH)

        try:
            from tabpfn import TabPFNRegressor
            from tabpfn.constants import ModelVersion
        except ImportError as exc:
            raise RuntimeError(f"无法在 {TABPFN_PATH} 找到 tabpfn 模块") from exc

        cls._tabpfn_regressor_class = TabPFNRegressor
        cls._model_version_class = ModelVersion
