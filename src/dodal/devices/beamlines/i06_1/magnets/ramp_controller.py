from dataclasses import dataclass
from functools import cached_property

from ophyd_async.core import (
    InstantMovableMock,
    MovableLogic,
    SignalR,
    StandardMovable,
    StandardReadable,
    StandardReadableFormat,
    TimeoutCalculator,
    default_mock_class,
    set_mock_value,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw


@dataclass
class RampRateMovableLogic(MovableLogic[float]):
    limit: SignalR[float]

    async def check_move(self, new_position: float) -> None:
        limit = await self.limit.get_value()
        if new_position > limit:
            raise ValueError(
                f"Requested ramp rate {new_position} exceeds the maximum limit of {limit} for device {self.readback.name}."
            )

    async def move(self, new_position: float, timeout: TimeoutCalculator):
        await self.setpoint.set(new_position, timeout=timeout())


class MockMagnetAxisRampRateController(InstantMovableMock):
    async def connect(self, device: StandardMovable):
        await super().connect(device)
        # Extend to set a sensible default value for the limit.
        set_mock_value(device.limit, 2)  # type: ignore


@default_mock_class(MockMagnetAxisRampRateController)
class MagnetAxisRampRateController(StandardMovable[float], StandardReadable):
    """Controls the ramp rate of a single superconducting magnet axis.

    Exposes the readback ramp rate, demand ramp rate and the maximum
    permitted ramp rate for one magnet axis.
    """

    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.readback = epics_signal_r(float, prefix + "STS:RAMPRATE:TPM")
        self.demand = epics_signal_rw(float, prefix + "SET:DMD:RAMPRATE:TPM")
        self.ramp_limit = epics_signal_r(float, prefix + "LIM:RAMPRATE:TPM")
        self.axis_limit = epics_signal_r(float, prefix + "LIM:FIELD:NOW")
        super().__init__(name)

    @cached_property
    def movable_logic(self) -> RampRateMovableLogic:
        return RampRateMovableLogic(
            readback=self.readback, setpoint=self.demand, limit=self.ramp_limit
        )


class MagnetThreeAxesRampRateController(StandardReadable):
    """Groups the ramp rate controllers for the x, y and z magnet axes.

    This device is passed to :class:`SuperConductingMagnetController` so that each
    :class:`MagnetAxis` can configure its own ramp rate during preparation for
    fly scans.
    """

    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.x = MagnetAxisRampRateController(prefix + "-01:")
            self.y = MagnetAxisRampRateController(prefix + "-02:")
            self.z = MagnetAxisRampRateController(prefix + "-03:")

        super().__init__(name)
