from ophyd_async.core import (
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw


class PumpControl(StrictEnum):
    MANUAL = "Manual"
    AUTO = "Auto"


# TODO: Make use of Status PV:
# https://github.com/DiamondLightSource/dodal/issues/338
class Linkam3(StandardReadable):
    """Device to represent a Linkam3 temperature controller

    Attributes:
        tolerance (float): Deadband around the setpoint within which the position is assumed to have been reached
        settle_time (int): The delay between reaching the setpoint and the move being considered complete

    Args:
        prefix (str): PV prefix for this device
        name (str): unique name for this device
    """

    tolerance: float = 0.5
    settle_time: int = 0

    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.temp = epics_signal_r(float, prefix + "TEMP")
        with self.add_children_as_readables():
            self.dsc = epics_signal_r(float, prefix + "DSC")
            self.start_heat = epics_signal_rw(bool, prefix + "STARTHEAT")

            self.ramp_rate = epics_signal_rw(
                float, prefix + "RAMPRATE", prefix + "RAMPRATE:SET"
            )
            self.ramp_time = epics_signal_r(float, prefix + "RAMPTIME")
            self.set_point = epics_signal_rw(
                float, prefix + "SETPOINT", prefix + "SETPOINT:SET"
            )
            self.pump_control = epics_signal_r(
                PumpControl,
                prefix + "LNP_MODE:SET",
            )
            self.speed = epics_signal_rw(
                float, prefix + "LNP_SPEED", prefix + "LNP_SPEED:SET"
            )

            self.chamber_vac = epics_signal_r(float, prefix + "VAC_CHAMBER")
            self.sensor_vac = epics_signal_r(float, prefix + "VAC_DATA1")

            self.error = epics_signal_r(str, prefix + "CTRLLR:ERR")

        super().__init__(name=name)
