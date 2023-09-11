import math
from time import sleep, time

from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO, Kind
from ophyd.status import DeviceStatus

from dodal.log import LOGGER


class Transfocator(Device):
    """The transfocator is a device that puts a number of lenses in the beam to change
    its shape.

    The vertical beamsize can be set using:
        my_transfocator = Transfocator(name="t")
        vert_beamsize_microns = 20
        my_transfocator.set(vert_beamsize_microns)
    """

    beamsize_set_microns: EpicsSignal = Cpt(EpicsSignal, "VERT_REQ", kind=Kind.hinted)
    predicted_vertical_num_lenses: EpicsSignal = Cpt(EpicsSignal, "LENS_PRED")

    number_filters_sp: EpicsSignal = Cpt(EpicsSignal, "NUM_FILTERS")

    start: EpicsSignal = Cpt(EpicsSignal, "START.PROC")
    start_rbv: EpicsSignalRO = Cpt(EpicsSignalRO, "START_RBV")

    vertical_lens_rbv: EpicsSignalRO = Cpt(EpicsSignalRO, "VER", kind=Kind.hinted)

    TIMEOUT = 120
    _POLLING_WAIT = 0.01

    def polling_wait_on_start_rbv(self, for_value):
        # For some reason couldn't get monitors working on START_RBV
        # (See https://github.com/DiamondLightSource/dodal/issues/152)
        start_time = time()
        while time() < start_time + self.TIMEOUT:
            RBV_value = self.start_rbv.get()
            if RBV_value == for_value:
                return
            sleep(self._POLLING_WAIT)

        # last try
        if self.start_rbv.get() != for_value:
            raise TimeoutError()

    def set(self, beamsize_microns: float) -> DeviceStatus:
        """To set the beamsize on the transfocator we must:
        1. Set the beamsize in the calculator part of the transfocator
        2. Get the predicted number of lenses needed from this calculator
        3. Enter this back into the device
        4. Start the device moving
        5. Wait for the start_rbv goes high and low again
        """
        subscriber: int
        status = DeviceStatus(self, timeout=self.TIMEOUT)

        def set_based_on_predicition(old_value, value, *args, **kwargs):
            if not math.isclose(old_value, value, abs_tol=1e-8):
                self.predicted_vertical_num_lenses.unsubscribe(subscriber)

                # We can only put an integer number of lenses in the beam but the
                # calculation in the IOC returns the theoretical float number of lenses
                value = round(value)
                LOGGER.info(f"Transfocator setting {value} filters")
                self.number_filters_sp.set(value).wait()
                self.start.set(1).wait()
                self.polling_wait_on_start_rbv(1)
                self.polling_wait_on_start_rbv(0)
            # The value hasn't changed so assume the device is already set up correctly
            status.set_finished()

        LOGGER.info(f"Transfocator setting {beamsize_microns} beamsize")
        if self.beamsize_set_microns.get() != beamsize_microns:
            subscriber = self.predicted_vertical_num_lenses.subscribe(
                set_based_on_predicition, run=False
            )
            self.beamsize_set_microns.set(beamsize_microns)
        else:
            status.set_finished()
        return status
