from ophyd_async.core import DeviceVector, StandardReadable
from ophyd_async.epics.motion import Motor


class S4SlitGaps(StandardReadable):
    """
    Representation of S4 Slit Gaps, a group of motors controlling the xray optics slits
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
    """
    A group of slits, since they normally come in groups following a standard PV naming
    convention.
    """

    def __init__(
        self,
        prefix: str,
        indices: range,
        name: str = "",
    ) -> None:
        """
        Constructor, formats prefix with indices for sub-devices. For example:
        S4SlitGapsGroup("MY-SLITS-{0:02d}:", range(5)) will populate the group with 4
        S4SlitGaps devices with prefixes MY-SLITS-00, MY-SLITS-01, MY-SLITS-02,
        MY-SLITS-03. The index to access them will be the same as the PV number, so
        MY-SLITS-02 is accessed via group.slits[2].

        Args:
            prefix: PV prefix with python formatting
            indices: Indices of individual slits
            name: Device name. Defaults to "".
        """

        self.slits: DeviceVector[S4SlitGaps] = DeviceVector(
            {i: S4SlitGaps(prefix.format(i)) for i in indices}
        )
        # Type ignore pending: https://github.com/bluesky/ophyd-async/issues/192
        self.set_readable_signals(read=self.slits.values())  # type: ignore
        super().__init__(name)
