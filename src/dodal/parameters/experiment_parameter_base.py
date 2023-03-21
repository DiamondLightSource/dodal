from abc import ABC, abstractmethod


class AbstractExperimentParameterBase(ABC):
    @abstractmethod
    def get_num_images(self):
        pass
