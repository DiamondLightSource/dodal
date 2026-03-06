from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
)
from ophyd_async.epics.core import epics_signal_rw


class AttenuatorPositions(StrictEnum):
    TRANS_100 = "100%"
    TRANS_50 = "50%"
    TRANS_10 = "10%"
    TRANS_1 = "1%"
    TRANS_0_1 = "0.1%"
    TRANS_0_01 = "0.01%"
    TRANS_0_001 = "0.001%"

    @classmethod
    def from_float(cls, value):
        string_representation = f"{value}%"
        try:
            return AttenuatorPositions(string_representation)
        except ValueError as e:
            raise ValueError(
                f"{string_representation} is not a valid transmission. Options are {', '.join([a.value for a in AttenuatorPositions])}"
            ) from e


class Attenuator(StandardReadable, Movable[float | AttenuatorPositions]):
    """A device to change the attenuation of the beam.

    This can be done by doing:

    >>> bps.mv(attenuator, 10)
    or
    >>> bps.mv(attenuator, AttenuatorPositions.TRANS_10)

    Where 10 is the transmission in percent.

    There are only a specific set of transmissions that can be selected. The allowed list
    can be found by doing `list(AttenuatorPositions)`
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.transmission = epics_signal_rw(
                AttenuatorPositions, f"{prefix}MP1:SELECT"
            )
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: float | AttenuatorPositions):
        """Change the transmission to the specified percentage.

        Will raise an error if the percentage is not possible.
        """
        if isinstance(value, float) or isinstance(value, int):
            value = AttenuatorPositions.from_float(value)
        await self.transmission.set(value)
