from time import sleep

from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO, Kind
from ophyd.status import DeviceStatus
from dodal.log import LOGGER


class Transfocator(Device):
    beamsize_set: EpicsSignal = Cpt(EpicsSignal, "VERT_REQ", kind=Kind.hinted)
    predict_vertical: EpicsSignal = Cpt(EpicsSignal, "LENS_PRED")

    number_filters_sp: EpicsSignal = Cpt(EpicsSignal, "NUM_FILTERS")

    start: EpicsSignal = Cpt(EpicsSignal, "START.PROC")
    start_rbv: EpicsSignalRO = Cpt(EpicsSignalRO, "START_RBV")

    vertical_lens_rbv: EpicsSignalRO = Cpt(EpicsSignalRO, "VER", kind=Kind.hinted)

    TIMEOUT = 120
    _POLLING_WAIT = 0.01

    def polling_wait_on_stat_rbv(self, for_value):
        # For some reason couldn't get monitors working on START_RBV
        # (See https://github.com/DiamondLightSource/dodal/issues/152)
        for _ in range(int(self.TIMEOUT / self._POLLING_WAIT)):
            RBV_value = self.start_rbv.get()
            sleep(self._POLLING_WAIT)
            if RBV_value == for_value:
                return
        raise TimeoutError()

    def set(self, beamsize: float) -> DeviceStatus:
        subscriber: int
        status = DeviceStatus(self, timeout=self.TIMEOUT)

        def set_based_on_predicition(old_value, value, *args, **kwargs):
            if old_value != value:
                self.predict_vertical.unsubscribe(subscriber)

                value = round(value)
                LOGGER.info(f"Transfocator setting {value} filters")
                self.number_filters_sp.set(value).wait()
                self.start.set(1).wait()
                self.polling_wait_on_stat_rbv(1)
                self.polling_wait_on_stat_rbv(0)
                status.set_finished()

        LOGGER.info(f"Transfocator setting {beamsize} beamsize")
        if self.beamsize_set.get() != beamsize:
            subscriber = self.predict_vertical.subscribe(
                set_based_on_predicition, run=False
            )
            self.beamsize_set.set(beamsize)
        else:
            status.set_finished()
        return status
