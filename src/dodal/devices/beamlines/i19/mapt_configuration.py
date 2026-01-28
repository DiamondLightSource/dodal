from ophyd_async.core import DeviceVector, SignalR, StandardReadable, SubsetEnum
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_x


class MAPTConfigurationTable(StandardReadable):
    """Readable device that can be used to build the read-only MAPT (Mini Apertures)
    configuration table in controls for aperture motors in the available positions.
    For each aperture it sets up a readable signal with the position of all the motors
    in the MAPT configuration.
    This device can be used to build the table for both eh1 and eh2 on I19, in
    combination with the MAPTConfigurationControl device.
    """

    def __init__(
        self, prefix: str, motor_name: str, aperture_list: list[int], name: str = ""
    ) -> None:
        with self.add_children_as_readables():
            self.in_positions: DeviceVector[SignalR[float]] = DeviceVector(
                {
                    pos: epics_signal_r(float, f"{prefix}:{pos}UM:{motor_name}")
                    for pos in aperture_list
                }
            )
        super().__init__(name)


class MAPTConfigurationControl(StandardReadable):
    """A device to control the MAPT (Mini Aperture) configuration. It provides a signal
    to set the configuration PV to the requested value and a triggerable signal that
    will move all the motors to the correct position."""

    def __init__(
        self, prefix: str, aperture_request: type[SubsetEnum], name: str = ""
    ) -> None:
        with self.add_children_as_readables():
            self.select_config = epics_signal_rw(aperture_request, f"{prefix}")
        self.apply_selection = epics_signal_x(f"{prefix}:APPLY.PROC")
        super().__init__(name)
