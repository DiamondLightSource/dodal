import asyncio
import math
import string

from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    DeviceMock,
    DeviceVector,
    SignalR,
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
    SubsetEnum,
    callback_on_mock_put,
    default_mock_class,
    set_and_wait_for_other_value,
    set_mock_value,
)
from ophyd_async.epics.core import (
    epics_signal_r,
    epics_signal_rw,
    epics_signal_w,
)
from ophyd_async.epics.motor import Motor


class FastAttenuatorState(StrictEnum):
    FAULT = "Fault"
    OUT = "Out"
    OPENING = "Opening"
    IN = "In"
    CLOSING = "Closing"


class FastAttenuatorDemand(SubsetEnum):
    IN = "In"
    OUT = "Out"


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

        self._underlying_motor = Motor(f"{prefix}Y")
        self._positions = DeviceVector[SignalR[float]](
            {
                i: epics_signal_r(float, f"{prefix}P1:VAL{letter}")
                for i, letter in enumerate(list(string.ascii_uppercase[:10]))
            }
        )
        self._timeout = 20
        super().__init__(name)

    async def _calculate_max_timeout(self) -> float:
        """Calculate the time needed to move between the two furthest apart positions."""
        motor_leeway = 2  # Add a small buffer to the calculated timeout
        values = await asyncio.gather(
            *(position.get_value() for position in self._positions.values())
        )
        non_zero_values = [value for value in values if not math.isclose(value, 0)]
        if not non_zero_values:
            return self._timeout
        max_distance = max(non_zero_values) - min(non_zero_values)
        velocity = await self._underlying_motor.velocity.get_value()
        return max_distance / velocity + motor_leeway

    async def connect(self, *args, **kwargs) -> None:
        await super().connect(*args, **kwargs)
        self._timeout = await self._calculate_max_timeout()

    @AsyncStatus.wrap
    async def set(self, value: SlowAttenuatorPositions):
        """Change the transmission to the specified percentage.

        Will raise ValueError if the percentage is not possible.
        """
        await self.transmission.set(value, timeout=self._timeout)


class MockFastAttenuator(DeviceMock["FastAttenuator"]):
    async def connect(self, device: "FastAttenuator") -> None:
        def set_readback(value: FastAttenuatorDemand, *_, **__):
            if value == FastAttenuatorDemand.IN:
                set_mock_value(device.status, FastAttenuatorState.IN)
            elif value == FastAttenuatorDemand.OUT:
                set_mock_value(device.status, FastAttenuatorState.OUT)

        callback_on_mock_put(device.control, set_readback)


@default_mock_class(MockFastAttenuator)
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
