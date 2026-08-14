import asyncio
from dataclasses import dataclass
from typing import Generic

from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, Reference, StandardReadable, wait_for_value

from dodal.devices.insertion_device.enum import UndulatorGateStatus
from dodal.devices.insertion_device.undulator.access_control import (
    UndulatorAccessControl,
)
from dodal.devices.insertion_device.undulator.gap import UndulatorGap
from dodal.devices.insertion_device.undulator.phase_axes import (
    Apple2LockedPhasesVal,
    Apple2PhasesVal,
    PhaseAxesType,
)
from dodal.log import LOGGER


@dataclass
class Apple2Val:
    gap: float
    phase: Apple2LockedPhasesVal | Apple2PhasesVal


class Apple2(StandardReadable, Movable[Apple2Val], Generic[PhaseAxesType]):
    """Device representing the combined motor controls for an Apple2 undulator.

    Attributes:
        gap_ref (Reference[UndulatorGap]): The undulator gap motor device.
        phase_ref (Reference[UndulatorPhaseAxes]): The undulator phase axes device,
            consisting offour phase motors.

    Args:
        gap (UndulatorGap): An UndulatorGap device.
        phase (UndulatorPhaseAxes): An UndulatorPhaseAxes device.
        name (str, optional): Name of the device.
    """

    def __init__(
        self,
        gap: UndulatorGap,
        phase: PhaseAxesType,
        access_control: UndulatorAccessControl,
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.gap_ref = Reference(gap)
            self.phase_ref = Reference(phase)
            self.access_control_ref = Reference(access_control)
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, id_motor_values: Apple2Val) -> None:
        """Check ID is in a movable state and set all the demand value before moving
        them all at the same time.
        """
        gap = self.gap_ref()
        phase = self.phase_ref()
        access_control = self.access_control_ref()

        LOGGER.info(f"Moving {self.name} apple2 motors to {id_motor_values}")
        await access_control.check_value()
        await asyncio.gather(
            gap.set_demand_positions(id_motor_values.gap),
            phase.set_demand_positions(id_motor_values.phase),
        )
        timeout = max(await asyncio.gather(gap.get_timeout(), phase.get_timeout()))
        await asyncio.gather(
            gap.set_move.set(value=1, timeout=timeout),
            phase.set_move.set(value=1, timeout=timeout),
        )
        await wait_for_value(
            access_control.gate, UndulatorGateStatus.CLOSE, timeout=timeout
        )
