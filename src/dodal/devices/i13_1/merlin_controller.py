import asyncio

from ophyd_async.core import (
    DetectorTrigger,
    TriggerInfo,
)
from ophyd_async.epics.adcore import (
    ADBaseController,
    ADImageMode,
)

from .merlin_driver_io import MerlinDriverIO, MerlinTriggerMode


class MerlinController(ADBaseController[MerlinDriverIO]):
    """MerlinController for a MerlinDriverIO"""

    def get_deadtime(self, exposure: float | None) -> float:
        return 1.64e-3

    async def prepare(self, trigger_info: TriggerInfo):
        if (exposure := trigger_info.livetime) is not None:
            await self.driver.acquire_time.set(exposure)
            # await self.driver.acquire_period.set(exposure + trigger_info.deadtime)
            await self.driver.acquire_period.set(exposure)

        if trigger_info.trigger is DetectorTrigger.INTERNAL:
            await self.driver.trigger_mode.set(MerlinTriggerMode.INTERNAL)
        elif trigger_info.trigger in {
            DetectorTrigger.CONSTANT_GATE,
            DetectorTrigger.EDGE_TRIGGER,
        }:
            await self.driver.trigger_mode.set(MerlinTriggerMode.START_RISING)
        else:
            # CONSTANT_GATE not in ADMerlin.  When configuring from Windows NI software,
            # a stop trigger can be used in additon to the start trigger.
            raise ValueError(f"ADMerlin does not support {trigger_info.trigger}")

        await asyncio.gather(
            self.driver.num_images.set(trigger_info.total_number_of_exposures),
            self.driver.image_mode.set(ADImageMode.MULTIPLE),
        )
