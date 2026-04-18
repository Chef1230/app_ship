from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


class BasePredictor(ABC):
    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series) -> "BasePredictor":
        raise NotImplementedError

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        raise NotImplementedError


class SklearnRegressorAdapter(BasePredictor):
    def __init__(self, regressor: Any) -> None:
        self.regressor = regressor
        self.model: Pipeline | DummyRegressor | None = None
        self.no_feature_mode = False

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "SklearnRegressorAdapter":
        X = self._prepare_features(X)
        y = pd.Series(y).astype(float)

        if X.shape[1] == 0:
            self.no_feature_mode = True
            self.model = DummyRegressor(strategy="mean")
            self.model.fit(np.zeros((len(y), 1)), y)
            return self

        self.no_feature_mode = False
        numeric_columns = X.select_dtypes(include=["number", "bool"]).columns.tolist()
        categorical_columns = [column for column in X.columns if column not in numeric_columns]

        transformers = []
        if numeric_columns:
            transformers.append(
                (
                    "numeric",
                    Pipeline([("imputer", SimpleImputer(strategy="median"))]),
                    numeric_columns,
                )
            )
        if categorical_columns:
            transformers.append(
                (
                    "categorical",
                    Pipeline(
                        [
                            ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
                            ("onehot", self._one_hot_encoder()),
                        ]
                    ),
                    categorical_columns,
                )
            )

        self.model = Pipeline(
            [
                ("preprocess", ColumnTransformer(transformers, remainder="drop")),
                ("regressor", clone(self.regressor)),
            ]
        )
        self.model.fit(X, y)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if self.model is None:
            raise RuntimeError("模型尚未训练")

        X = self._prepare_features(X)
        if self.no_feature_mode:
            return self.model.predict(np.zeros((len(X), 1)))

        return self.model.predict(X)

    def _prepare_features(self, X: pd.DataFrame) -> pd.DataFrame:
        if isinstance(X, pd.DataFrame):
            return X.copy()
        return pd.DataFrame(X)

    @staticmethod
    def _one_hot_encoder() -> OneHotEncoder:
        try:
            return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        except TypeError:
            return OneHotEncoder(handle_unknown="ignore", sparse=False)
