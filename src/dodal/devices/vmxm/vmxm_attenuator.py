from typing import Optional

from ophyd import Component, Device, EpicsSignal, Kind
from ophyd.status import Status, SubscriptionStatus

from dodal.devices.detector import DetectorParams
from dodal.devices.status import await_value
from dodal.log import LOGGER


class VmxmAttenuator(Device):
    """Any reference to transmission (both read and write) in this Device is fraction
    e.g. 0-1"""

    def set(self, transmission: float) -> SubscriptionStatus:
        """Set the transmission to the fractional value given.
        Args:
            transmission (float): A fraction to set transmission to between 0-1
        Get desired states and calculated states, return a status which is complete once they are equal
        """

        LOGGER.info("Using current energy ")
        self.use_current_energy.set(1).wait()
        LOGGER.info(f"Setting desired transmission to {transmission}")
        self.desired_transmission.set(transmission).wait()
        LOGGER.info("Sending change filter command")
        self.change.set(1).wait()

        status = Status(done=True, success=True)
        status &= await_value(self.filter1_inpos, 1, timeout=10)
        status &= await_value(self.filter2_inpos, 1, timeout=10)
        status &= await_value(self.filter3_inpos, 1, timeout=10)
        status &= await_value(self.filter4_inpos, 1, timeout=10)
        return status

    desired_transmission: EpicsSignal = Component(EpicsSignal, "T2A:SETVAL1")
    use_current_energy: EpicsSignal = Component(
        EpicsSignal, "E2WL:USECURRENTENERGY.PROC"
    )
    actual_transmission: EpicsSignal = Component(EpicsSignal, "MATCH", kind=Kind.hinted)

    detector_params: Optional[DetectorParams] = None

    filter1_inpos: EpicsSignal = Component(EpicsSignal, "MP1:INPOS")
    filter2_inpos: EpicsSignal = Component(EpicsSignal, "MP2:INPOS")
    filter3_inpos: EpicsSignal = Component(EpicsSignal, "MP3:INPOS")
    filter4_inpos: EpicsSignal = Component(EpicsSignal, "MP4:INPOS")
