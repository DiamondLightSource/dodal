from abc import ABC, abstractmethod

from dodal.devices.eiger import EigerTriggerNumber


class AbstractExperimentParameterBase(ABC):
    trigger_number: EigerTriggerNumber = NotImplemented

    @abstractmethod
    def get_num_images(self):
        pass
