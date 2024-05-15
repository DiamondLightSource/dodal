from enum import Enum

from ophyd_async.core import ConfigSignal, StandardReadable, soft_signal_r_and_setter
from ophyd_async.epics.motion import Motor
from ophyd_async.epics.signal import epics_signal_r

# The acceptable difference, in mm, between the undulator gap and the DCM
# energy, when the latter is converted to mm using lookup tables
UNDULATOR_DISCREPANCY_THRESHOLD_MM = 2e-3


class UndulatorGapAccess(str, Enum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


class Undulator(StandardReadable):
    """
    An Undulator-type insertion device, used to control photon emission at a given
    beam energy.
    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
        poles: int | None = None,
        length: float | None = None,
    ) -> None:
        """Constructor

        Args:
            prefix: PV prefix
            poles (int): Number of magnetic poles built into the undulator
            length (float): Length of the undulator in meters
            name (str, optional): Name for device. Defaults to "".
        """

        with self.add_children_as_readables():
            self.gap_motor = Motor(prefix + "BLGAPMTR")
            self.current_gap = epics_signal_r(float, prefix + "CURRGAPD")
            self.gap_access = epics_signal_r(UndulatorGapAccess, prefix + "IDBLENA")

        with self.add_children_as_readables(ConfigSignal):
            self.gap_discrepancy_tolerance_mm, _ = soft_signal_r_and_setter(
                float,
                initial_value=UNDULATOR_DISCREPANCY_THRESHOLD_MM,
            )
            if poles is not None:
                self.poles, _ = soft_signal_r_and_setter(
                    int,
                    initial_value=poles,
                )
            else:
                self.poles = None

            if length is not None:
                self.length, _ = soft_signal_r_and_setter(
                    float,
                    initial_value=length,
                )
            else:
                self.length = None

        super().__init__(name)
