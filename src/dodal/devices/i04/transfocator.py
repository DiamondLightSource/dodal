import asyncio
import math

from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
    observe_value,
    wait_for_value,
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
            self.predicted_vertical_num_lenses = epics_signal_rw(
                float, prefix + "LENS_PRED"
            )
            self.number_filters_sp = epics_signal_rw(int, prefix + "NUM_FILTERS")
            self.start = epics_signal_rw(int, prefix + "START.PROC")
            self.start_rbv = epics_signal_r(int, prefix + "START_RBV")
            self.vertical_lens_rbv = epics_signal_r(float, prefix + "VER")

        self.TIMEOUT = 120

        super().__init__(name=name)

    async def _observe_beamsize_microns(self):
        is_set_filters_done = False

        async def set_based_on_prediction(value: float):
            if not math.isclose(
                self.latest_pred_vertical_num_lenses, value, abs_tol=1e-8
            ):
                # We can only put an integer number of lenses in the beam but the
                # calculation in the IOC returns the theoretical float number of lenses
                nonlocal is_set_filters_done
                value = round(value)
                LOGGER.info(f"Transfocator setting {value} filters")
                await self.number_filters_sp.set(value)
                await self.start.set(1)
                LOGGER.info("Waiting for start_rbv to change to 1")
                await wait_for_value(self.start_rbv, 1, self.TIMEOUT)
                LOGGER.info("Waiting for start_rbv to change to 0")
                await wait_for_value(self.start_rbv, 0, self.TIMEOUT)
                self.latest_pred_vertical_num_lenses = value
                is_set_filters_done = True

        # The value hasn't changed so assume the device is already set up correctly
        async for value in observe_value(self.predicted_vertical_num_lenses):
            await set_based_on_prediction(value)
            if is_set_filters_done:
                break

    @AsyncStatus.wrap
    async def set(self, value: float):
        """To set the beamsize on the transfocator we must:
        1. Set the beamsize in the calculator part of the transfocator
        2. Get the predicted number of lenses needed from this calculator
        3. Enter this back into the device
        4. Start the device moving
        5. Wait for the start_rbv goes high and low again
        """
        self.latest_pred_vertical_num_lenses = (
            await self.predicted_vertical_num_lenses.get_value()
        )

        LOGGER.info(f"Transfocator setting {value} beamsize")

        if await self.beamsize_set_microns.get_value() != value:
            # Logic in the IOC calculates predicted_vertical_num_lenses when beam_set_microns changes
            await asyncio.gather(
                self.beamsize_set_microns.set(value),
                self._observe_beamsize_microns(),
            )

        number_filters_rbv, vertical_lens_size_rbv = await asyncio.gather(
            self.number_filters_sp.get_value(),
            self.vertical_lens_rbv.get_value(),
        )

        LOGGER.info(
            f"Transfocator set complete. Number of filters is: {number_filters_rbv} and Vertical beam size is: {vertical_lens_size_rbv}"
        )
