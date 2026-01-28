import asyncio

from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
    observe_value,
    wait_for_value,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.common.device_utils import periodic_reminder
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
        self._vert_size_calc_sp = epics_signal_rw(float, prefix + "VERT_REQ")
        self._num_lenses_calc_rbv = epics_signal_r(float, prefix + "LENS_PRED")
        self.start = epics_signal_rw(int, prefix + "START.PROC")
        self.start_rbv = epics_signal_r(int, prefix + "START_RBV")

        with self.add_children_as_readables():
            self.number_filters_sp = epics_signal_rw(int, prefix + "NUM_FILTERS")
            self.current_horizontal_size_rbv = epics_signal_r(float, prefix + "HOR")
            self.current_vertical_size_rbv = epics_signal_r(float, prefix + "VER")

        self.TIMEOUT = 120

        super().__init__(name=name)

    async def set_based_on_prediction(self, value: float):
        # We can only put an integer number of lenses in the beam but the
        # calculation in the IOC returns the theoretical float number of lenses
        value = round(value)
        await self.number_filters_sp.set(value)
        await self.start.set(1)
        await wait_for_value(self.start_rbv, 1, self.TIMEOUT)
        await wait_for_value(self.start_rbv, 0, self.TIMEOUT)

    @AsyncStatus.wrap
    async def set(self, value: float):
        """To set the beamsize on the transfocator we must:
        1. Set the beamsize in the calculator part of the transfocator
        2. Get the predicted number of lenses needed from this calculator
        3. Enter this back into the device
        4. Start the device moving
        5. Wait for the start_rbv goes high and low again
        """
        LOGGER.info(f"Transfocator setting {value} beamsize")

        # Logic in the IOC calculates _num_lenses_calc_rbv when _vert_size_calc_sp changes

        # Register an observer before setting _vert_size_calc_sp to ensure we don't miss changes
        num_lenses_calc_iterator = observe_value(
            self._num_lenses_calc_rbv, timeout=self.TIMEOUT
        )

        await anext(num_lenses_calc_iterator)
        await self._vert_size_calc_sp.set(value)
        calc_lenses = await anext(num_lenses_calc_iterator)

        async with periodic_reminder(
            f"Waiting for transfocator to insert {calc_lenses} into beam"
        ):
            await self.set_based_on_prediction(calc_lenses)

        number_filters_rbv, vertical_lens_size_rbv = await asyncio.gather(
            self.number_filters_sp.get_value(),
            self.current_vertical_size_rbv.get_value(),
        )

        LOGGER.info(
            f"Transfocator set complete. Number of filters is: {number_filters_rbv} and Vertical beam size is: {vertical_lens_size_rbv}"
        )
