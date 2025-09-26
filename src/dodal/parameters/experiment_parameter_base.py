from abc import ABC

from pydantic import BaseModel


class AbstractExperimentParameterBase(BaseModel, ABC):
    pass


class AbstractExperimentWithBeamParams(AbstractExperimentParameterBase):
    transmission_fraction: float
