from typing import Optional

from ophyd import Component, Device, EpicsSignal, EpicsSignalRO, Kind
from ophyd.status import Status, SubscriptionStatus

from dodal.devices.detector import DetectorParams
from dodal.devices.status import await_value
from dodal.log import LOGGER


class AtteunatorFilter(Device):
    actual_filter_state: EpicsSignalRO = Component(EpicsSignalRO, ":INLIM")


class Attenuator(Device):
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
        actual_states = self.get_actual_filter_state_list()
        calculated_states = self.get_calculated_filter_state_list()
        for i in range(16):
            status &= await_value(
                actual_states[i], calculated_states[i].get(), timeout=10
            )
        return status

    calulated_filter_state_1: EpicsSignalRO = Component(EpicsSignalRO, "DEC_TO_BIN.B0")
    calulated_filter_state_2: EpicsSignalRO = Component(EpicsSignalRO, "DEC_TO_BIN.B1")
    calulated_filter_state_3: EpicsSignalRO = Component(EpicsSignalRO, "DEC_TO_BIN.B2")
    calulated_filter_state_4: EpicsSignalRO = Component(EpicsSignalRO, "DEC_TO_BIN.B3")
    calulated_filter_state_5: EpicsSignalRO = Component(EpicsSignalRO, "DEC_TO_BIN.B4")
    calulated_filter_state_6: EpicsSignalRO = Component(EpicsSignalRO, "DEC_TO_BIN.B5")
    calulated_filter_state_7: EpicsSignalRO = Component(EpicsSignalRO, "DEC_TO_BIN.B6")
    calulated_filter_state_8: EpicsSignalRO = Component(EpicsSignalRO, "DEC_TO_BIN.B7")
    calulated_filter_state_9: EpicsSignalRO = Component(EpicsSignalRO, "DEC_TO_BIN.B8")
    calulated_filter_state_10: EpicsSignalRO = Component(EpicsSignalRO, "DEC_TO_BIN.B9")
    calulated_filter_state_11: EpicsSignalRO = Component(EpicsSignalRO, "DEC_TO_BIN.BA")
    calulated_filter_state_12: EpicsSignalRO = Component(EpicsSignalRO, "DEC_TO_BIN.BB")
    calulated_filter_state_13: EpicsSignalRO = Component(EpicsSignalRO, "DEC_TO_BIN.BC")
    calulated_filter_state_14: EpicsSignalRO = Component(EpicsSignalRO, "DEC_TO_BIN.BD")
    calulated_filter_state_15: EpicsSignalRO = Component(EpicsSignalRO, "DEC_TO_BIN.BE")
    calulated_filter_state_16: EpicsSignalRO = Component(EpicsSignalRO, "DEC_TO_BIN.BF")

    filter_1: AtteunatorFilter = Component(AtteunatorFilter, "FILTER1")
    filter_2: AtteunatorFilter = Component(AtteunatorFilter, "FILTER2")
    filter_3: AtteunatorFilter = Component(AtteunatorFilter, "FILTER3")
    filter_4: AtteunatorFilter = Component(AtteunatorFilter, "FILTER4")
    filter_5: AtteunatorFilter = Component(AtteunatorFilter, "FILTER5")
    filter_6: AtteunatorFilter = Component(AtteunatorFilter, "FILTER6")
    filter_7: AtteunatorFilter = Component(AtteunatorFilter, "FILTER7")
    filter_8: AtteunatorFilter = Component(AtteunatorFilter, "FILTER8")
    filter_9: AtteunatorFilter = Component(AtteunatorFilter, "FILTER9")
    filter_10: AtteunatorFilter = Component(AtteunatorFilter, "FILTER10")
    filter_11: AtteunatorFilter = Component(AtteunatorFilter, "FILTER11")
    filter_12: AtteunatorFilter = Component(AtteunatorFilter, "FILTER12")
    filter_13: AtteunatorFilter = Component(AtteunatorFilter, "FILTER13")
    filter_14: AtteunatorFilter = Component(AtteunatorFilter, "FILTER14")
    filter_15: AtteunatorFilter = Component(AtteunatorFilter, "FILTER15")
    filter_16: AtteunatorFilter = Component(AtteunatorFilter, "FILTER16")

    desired_transmission: EpicsSignal = Component(EpicsSignal, "T2A:SETVAL1")
    use_current_energy: EpicsSignal = Component(
        EpicsSignal, "E2WL:USECURRENTENERGY.PROC"
    )
    change: EpicsSignal = Component(EpicsSignal, "FANOUT")
    actual_transmission: EpicsSignal = Component(EpicsSignal, "MATCH", kind=Kind.hinted)

    detector_params: Optional[DetectorParams] = None

    def get_calculated_filter_state_list(self) -> list[EpicsSignal]:
        return [
            self.calulated_filter_state_1,
            self.calulated_filter_state_2,
            self.calulated_filter_state_3,
            self.calulated_filter_state_4,
            self.calulated_filter_state_5,
            self.calulated_filter_state_6,
            self.calulated_filter_state_7,
            self.calulated_filter_state_8,
            self.calulated_filter_state_9,
            self.calulated_filter_state_10,
            self.calulated_filter_state_11,
            self.calulated_filter_state_12,
            self.calulated_filter_state_13,
            self.calulated_filter_state_14,
            self.calulated_filter_state_15,
            self.calulated_filter_state_16,
        ]

    def get_actual_filter_state_list(self) -> list[EpicsSignal]:
        return [
            self.filter_1.actual_filter_state,
            self.filter_2.actual_filter_state,
            self.filter_3.actual_filter_state,
            self.filter_4.actual_filter_state,
            self.filter_5.actual_filter_state,
            self.filter_6.actual_filter_state,
            self.filter_7.actual_filter_state,
            self.filter_8.actual_filter_state,
            self.filter_9.actual_filter_state,
            self.filter_10.actual_filter_state,
            self.filter_11.actual_filter_state,
            self.filter_12.actual_filter_state,
            self.filter_13.actual_filter_state,
            self.filter_14.actual_filter_state,
            self.filter_15.actual_filter_state,
            self.filter_16.actual_filter_state,
        ]
