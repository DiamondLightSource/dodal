from typing import Generic, TypeVar

from ophyd_async.core import DetectorTriggerLogic
from ophyd_async.epics.adcore import (
    ADBaseIO,
    ADImageMode,
    prepare_exposures,
)

ADBaseIOT = TypeVar("ADBaseIOT", bound=ADBaseIO)


class ConfigurableImageModeTriggerLogic(DetectorTriggerLogic, Generic[ADBaseIOT]):
    def __init__(
        self, driver: ADBaseIOT, image_mode: ADImageMode = ADImageMode.MULTIPLE
    ):
        self.driver = driver
        self.image_mode = image_mode

    async def prepare_internal(self, num: int, livetime: float, deadtime: float):
        await self.driver.image_mode.set(self.image_mode)
        await prepare_exposures(self.driver, num, livetime, deadtime)
