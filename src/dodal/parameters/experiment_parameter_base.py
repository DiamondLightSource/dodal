from abc import ABC, abstractmethod


class AbstractExperimentParameterBase(ABC):
    pass


class AbstractExperimentWithBeamParams(AbstractExperimentParameterBase):
    transmission_fraction: float

    @abstractmethod
    def get_num_images(self) -> int:
        pass
