import math
import asyncio
from time import sleep, time

from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO, Kind
from ophyd.status import DeviceStatus

from ophyd_async.core import (
    StandardReadable,
    StandardReadableFormat,
    observe_value,
    AsyncStatus,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.log import LOGGER


class Transfocator(StandardReadable):
    """The transfocator is a device that puts a number of lenses in the beam to change
    its shape.

    The vertical beamsize can be set using:
        my_transfocator = Transfocator(name="t")
        vert_beamsize_microns = 20
        my_transfocator.set(vert_beamsize_microns)
    """

    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.beamsize_set_microns = epics_signal_rw(float, prefix + "VERT_REQ")
            self.predicted_vertical_num_lenses = epics_signal_rw(float, prefix + "LENS_PRED")
            self.number_filters_sp = epics_signal_rw(int, prefix + "NUM_FILTERS")

            self.start = epics_signal_rw(int, prefix + "START.PROC")
            self.start_rbv = epics_signal_r(int, prefix + "START_RBV")

            self.vertical_lens_rbv = epics_signal_r(float, prefix + "VER")

        self.TIMEOUT = 120
        self._POLLING_WAIT = 0.01

        super().__init__(name=name)

    async def _observe_beamsize_microns(self):
        have_we_done_it = False
        async def set_based_on_predicition(value: float):
            if not math.isclose(self.latest_pred_vertical_num_lenses, value, abs_tol=1e-8):
                # We can only put an integer number of lenses in the beam but the
                # calculation in the IOC returns the theoretical float number of lenses
                nonlocal have_we_done_it
                value = round(value)
                LOGGER.info(f"Transfocator setting {value} filters")
                await self.number_filters_sp.set(value)
                await self.start.set(1)
                await self.polling_wait_on_start_rbv(1)
                await self.polling_wait_on_start_rbv(0)
                self.latest_pred_vertical_num_lenses = value
                have_we_done_it = True
        # The value hasn't changed so assume the device is already set up correctly
        async for value in observe_value(self.predicted_vertical_num_lenses):
            await set_based_on_predicition(value)
            if have_we_done_it:
                break

    async def polling_wait_on_start_rbv(self, for_value):
        # For some reason couldn't get monitors working on START_RBV
        # (See https://github.com/DiamondLightSource/dodal/issues/152)
        start_time = time()
        while time() < start_time + self.TIMEOUT:
            RBV_value = await self.start_rbv.get_value()
            if RBV_value == for_value:
                return
            await asyncio.sleep(self._POLLING_WAIT)

        # last try
        if self.start_rbv.get_value() != for_value:
            raise TimeoutError()

    @AsyncStatus.wrap
    async def set(self, beamsize_microns: float) -> None:
        """To set the beamsize on the transfocator we must:
        1. Set the beamsize in the calculator part of the transfocator
        2. Get the predicted number of lenses needed from this calculator
        3. Enter this back into the device
        4. Start the device moving
        5. Wait for the start_rbv goes high and low again
        """
        self.latest_pred_vertical_num_lenses = await self.predicted_vertical_num_lenses.get_value()

        LOGGER.info(f"Transfocator setting {beamsize_microns} beamsize")

        if await self.beamsize_set_microns.get_value() != beamsize_microns:
            await asyncio.gather(self.beamsize_set_microns.set(beamsize_microns), self._observe_beamsize_microns())
