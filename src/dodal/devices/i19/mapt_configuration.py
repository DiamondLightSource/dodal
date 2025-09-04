from ophyd_async.core import DeviceVector, SignalR, StandardReadable
from ophyd_async.epics.signal import epics_signal_r


class MAPTConfiguration(StandardReadable):
    """Readable device that can be used to build the read-only MAPT configuration table
    for aperture motors in the available positions.
    Can be used for both eh1 and eh2 on I19.
    """

    def __init__(
        self, prefix: str, motor_name: str, aperture_list: list[int], name: str = ""
    ) -> None:
        with self.add_children_as_readables():
            self.in_positions: DeviceVector[SignalR[float]] = DeviceVector(
                {
                    pos: epics_signal_r(float, f"{prefix}{pos}UM:{motor_name}")
                    for pos in aperture_list
                }
            )
        super().__init__(name)
