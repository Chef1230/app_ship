from __future__ import annotations

from sklearn.ensemble import RandomForestRegressor

from models.base_model import SklearnRegressorAdapter


class RPTPredictor(SklearnRegressorAdapter):
    def __init__(self) -> None:
        super().__init__(
            RandomForestRegressor(
                n_estimators=80,
                random_state=42,
                min_samples_leaf=1,
            )
        )
