from __future__ import annotations

from sklearn.ensemble import ExtraTreesRegressor

from models.base_model import SklearnRegressorAdapter


class TabPFNPredictor(SklearnRegressorAdapter):
    def __init__(self) -> None:
        super().__init__(
            ExtraTreesRegressor(
                n_estimators=120,
                random_state=25,
                min_samples_leaf=1,
            )
        )
