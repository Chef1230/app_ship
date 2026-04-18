from __future__ import annotations

from models.base_model import BasePredictor
from models.rpt_predictor import RPTPredictor
from models.tabpfn_predictor import TabPFNPredictor


class ModelFactory:
    _MODELS = {
        "RPT": RPTPredictor,
        "TabPFN v2.5": TabPFNPredictor,
    }

    @classmethod
    def available_models(cls) -> list[str]:
        return list(cls._MODELS.keys())

    @classmethod
    def get_model(cls, model_name: str) -> BasePredictor:
        if model_name == "TabPFN":
            model_name = "TabPFN v2.5"

        predictor_class = cls._MODELS.get(model_name)
        if predictor_class is None:
            raise ValueError(f"不支持的模型：{model_name}")
        return predictor_class()
