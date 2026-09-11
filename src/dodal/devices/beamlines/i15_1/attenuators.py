from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
    SubsetEnum,
    set_and_wait_for_other_value,
)
from ophyd_async.epics.core import (
    epics_signal_r,
    epics_signal_rw,
    epics_signal_w,
)


class FastAttenuatorState(StrictEnum):
    FAULT = "Fault"
    OUT = "Open"
    OPENING = "Opening"
    IN = "Closed"
    CLOSING = "Closing"


class FastAttenuatorDemand(SubsetEnum):
    IN = "Close"
    OUT = "Open"


class SlowAttenuatorPositions(StrictEnum):
    TRANS_100 = "100%"
    TRANS_50 = "50%"
    TRANS_10 = "10%"
    TRANS_1 = "1%"
    TRANS_0_1 = "0.1%"
    TRANS_0_01 = "0.01%"
    TRANS_0_001 = "0.001%"

    @classmethod
    def from_trans_float(cls, trans: float) -> "SlowAttenuatorPositions":
        for position in cls:
            if float(position.value.rstrip("%")) == trans:
                return position
        supported_transmissions = ", ".join(position.value for position in cls)
        raise ValueError(
            f"Unsupported transmission: {trans}. "
            f"Supported transmissions are: {supported_transmissions}"
        )


class SlowAttenuator(StandardReadable, Movable[SlowAttenuatorPositions]):
    """A device to change the attenuation of the beam.

    This can be done by doing:

    >>> bps.mv(slow_attenuator, SlowAttenuatorPositions.TRANS_10)

    Where 10 is the transmission in percent.

    There are only a specific set of transmissions that can be selected. The allowed list
    can be found by doing `list(AttenuatorPositions)`
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.transmission = epics_signal_rw(
                SlowAttenuatorPositions, f"{prefix}MP1:SELECT"
            )
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: SlowAttenuatorPositions):
        """Change the transmission to the specified percentage.

        Will raise ValueError if the percentage is not possible.
        """
        await self.transmission.set(value)


class FastAttenuator(StandardReadable, Movable[FastAttenuatorDemand]):
    """A pneumatic attenuator that can quickly be put into the beam.

    This can be done by doing:

    >>> bps.mv(fast_attenuator, FastAttenuatorDemand.IN)
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        self.control = epics_signal_w(FastAttenuatorDemand, f"{prefix}CON")
        with self.add_children_as_readables():
            self.status = epics_signal_r(FastAttenuatorState, f"{prefix}STA")
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: FastAttenuatorDemand):
        """Move the attenuator In/Out."""
        match value:
            case FastAttenuatorDemand.IN:
                expected_readback = FastAttenuatorState.IN
            case FastAttenuatorDemand.OUT:
                expected_readback = FastAttenuatorState.OUT

        await set_and_wait_for_other_value(
            self.control, value, self.status, expected_readback
        )
