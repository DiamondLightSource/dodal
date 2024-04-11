from typing import Mapping

from ophyd_async.core import DeviceVector, StandardReadable
from ophyd_async.epics.motion import Motor


class S4SlitGaps(StandardReadable):
    """
    Representation of S4 Slit Gaps
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        self.x_gap = Motor(prefix + "X:SIZE")
        self.y_gap = Motor(prefix + "Y:SIZE")
        self.x_centre = Motor(prefix + "X:CENTRE")
        self.y_centre = Motor(prefix + "Y:CENTRE")

        # Type ignore pending: https://github.com/bluesky/ophyd-async/issues/192
        self.set_readable_signals(
            read=[
                self.x_gap,
                self.y_gap,
                self.x_centre,
                self.y_centre,
            ]  # type: ignore
        )
        super().__init__(name)


class S4SlitGapsGroup(StandardReadable):
    def __init__(
        self,
        prefix: str,
        indices: range,
        name: str = "",
    ) -> None:
        self.slits: DeviceVector[S4SlitGaps] = DeviceVector(
            {i: S4SlitGaps(prefix.format(i)) for i in indices}
        )
        # Type ignore pending: https://github.com/bluesky/ophyd-async/issues/192
        self.set_readable_signals(read=self.slits.values())  # type: ignore
        super().__init__(name)
