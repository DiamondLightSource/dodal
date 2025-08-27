from ophyd_async.core import EnabledDisabled, OnOff, StrictEnum
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.robot import BartRobot


class ForceBit(StrictEnum):
    """
    Enumeration representing the force bit states for the laser robot.

    Attributes:
        ON: Represents the "On" state, using the value from OnOff.ON.
        NO: Represents a "No" state, indicating no force applied.
        OFF: Represents the "Off" state, using the value from OnOff.OFF.
    """

    ON = OnOff.ON.value
    NO = "No"
    OFF = OnOff.OFF.value


class LaserRobot(BartRobot):
    """
    A device class representing a laser robot with control over various hardware components.

    Inherits from:
        BartRobot

    Args:
        prefix (str): The EPICS PV prefix for the device.
        name (str, optional): The name of the device. Defaults to an empty string.

    Attributes:
        dewar_lid_heater: Read/write EPICS signal for enabling/disabling the dewar lid heater.
        cryojet_retract: Read/write EPICS signal for controlling the cryojet retraction.
        set_beamline_safe: Read/write EPICS signal for setting the beamline to a safe state.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        self.dewar_lid_heater = epics_signal_rw(
            EnabledDisabled, prefix + "DW_1_ENABLED", prefix + "DW_1_CTRL"
        )
        self.cryojet_retract = epics_signal_rw(ForceBit, prefix + "OP_24_FORCE_OPTION")
        self.set_beamline_safe = epics_signal_rw(
            ForceBit, prefix + "IP_16_FORCE_OPTION"
        )
        super().__init__(prefix, name)
