import asyncio
from typing import Optional, Tuple

from ophyd_async.core import (
    AsyncStatus,
    DetectorControl,
    DetectorTrigger,
    set_and_wait_for_value,
)
from ophyd_async.epics import adcore

from .pressurejumpcell_io import (
     PressureJumpCellDriverIO,
     PressureJumpCellAdcIO, 
     PressureJumpCellTriggerMode,
     PressureJumpCellAdcTriggerMode,
)


#TODO Find out what the deadtime should be and if it can be retrieved from the device
_HIGHEST_POSSIBLE_DEADTIME = 1e-3


class PressureJumpCellController(DetectorControl):
    
    def __init__(self, driver: PressureJumpCellDriverIO, adc: PressureJumpCellAdcIO) -> None:
        self._drv = driver
        self._adc = adc

    def get_deadtime(self, exposure: float | None) -> float:
        return _HIGHEST_POSSIBLE_DEADTIME

    async def arm(
        self,
        num: int = 0,
        trigger: DetectorTrigger = DetectorTrigger.internal,
        exposure: Optional[float] = None,
    ) -> AsyncStatus:
        if num == 0:
            image_mode = adcore.ImageMode.continuous
        else:
            image_mode = adcore.ImageMode.multiple
        if exposure is not None:
            await self._drv.acquire_time.set(exposure)

        trigger_mode, adc_trigger_mode = self._get_trigger_info(trigger)
        
        # trigger mode must be set first and on it's own!
        await self._drv.trigger_mode.set(trigger_mode)
        await self._adc.adc_trigger_mode.set(adc_trigger_mode)

        await asyncio.gather(
            self._drv.num_images.set(num),
            self._drv.image_mode.set(image_mode),
        )

        status = await set_and_wait_for_value(self._drv.acquire, True)
        return status

    def _get_trigger_info(
        self, trigger: DetectorTrigger
    ) -> Tuple[PressureJumpCellTriggerMode, PressureJumpCellAdcTriggerMode]:
        supported_trigger_types = (
            DetectorTrigger.edge_trigger,
            DetectorTrigger.internal,
        )
        if trigger not in supported_trigger_types:
            raise ValueError(
                f"{self.__class__.__name__} only supports the following trigger "
                f"types: {supported_trigger_types} but was asked to "
                f"use {trigger}"
            )
        if trigger == DetectorTrigger.internal:
            return (PressureJumpCellTriggerMode.internal, PressureJumpCellAdcTriggerMode.continuous)
        else:
            return (PressureJumpCellTriggerMode.external, PressureJumpCellAdcTriggerMode.single)

    async def disarm(self):
        await asyncio.gather( 
            adcore.stop_busy_record(self._drv.acquire, False, timeout=1),
            adcore.stop_busy_record(self._adc.acquire, False, timeout=1)
        )
