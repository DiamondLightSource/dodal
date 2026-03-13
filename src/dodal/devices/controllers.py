from typing import TypeVar

from ophyd_async.core import DetectorTriggerLogic, SignalDict
from ophyd_async.epics.adcore import ADBaseIO, ADImageMode, prepare_exposures

ADBaseIOT = TypeVar("ADBaseIOT", bound=ADBaseIO)


class ConstantDeadTimeTriggerLogic(DetectorTriggerLogic):
    """DetectorTriggerLogic with a configured constant deadtime."""

    def __init__(
        self,
        driver: ADBaseIO,
        deadtime: float,
        image_mode: ADImageMode = ADImageMode.MULTIPLE,
    ):
        # super().__init__(driver, image_mode=image_mode)
        self.driver = driver
        self.deadtime = deadtime

    def get_deadtime(self, config_values: SignalDict) -> float:
        return self.deadtime

    async def prepare_internal(self, num: int, livetime: float, deadtime: float):
        await prepare_exposures(self.driver, num, livetime, deadtime)
