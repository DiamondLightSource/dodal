from abc import ABC, abstractmethod

from pydantic import BaseModel


class AbstractExperimentParameterBase(BaseModel, ABC):
    pass


class AbstractExperimentWithBeamParams(AbstractExperimentParameterBase):
    transmission_fraction: float

    @abstractmethod
    def get_num_images(self) -> int:
        pass
