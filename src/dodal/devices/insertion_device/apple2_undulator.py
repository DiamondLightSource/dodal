import asyncio
from dataclasses import dataclass
from typing import Generic

from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, Reference, StandardReadable, wait_for_value

from dodal.devices.insertion_device.apple2_phase_axes import (
    Apple2LockedPhasesVal,
    Apple2PhasesVal,
    PhaseAxesType,
)
from dodal.devices.insertion_device.apple2_undulator_gap import UndulatorGap
from dodal.devices.insertion_device.enum import UndulatorGateStatus
from dodal.log import LOGGER


@dataclass
class Apple2Val:
    gap: float
    phase: Apple2LockedPhasesVal | Apple2PhasesVal

    def extract_phase_val(self):
        return self.phase


class Apple2(StandardReadable, Movable[Apple2Val], Generic[PhaseAxesType]):
    """Device representing the combined motor controls for an Apple2 undulator.

    Attributes:
        gap (UndulatorGap): The undulator gap motor device.
        phase (UndulatorPhaseAxes): The undulator phase axes device, consisting of four
            phase motors.

    Args:
        id_gap (UndulatorGap): An UndulatorGap device.
        id_phase (UndulatorPhaseAxes): An UndulatorPhaseAxes device.
        name (str, optional): Name of the device.
    """

    def __init__(self, id_gap: UndulatorGap, id_phase: PhaseAxesType, name=""):
        with self.add_children_as_readables():
            self.gap_ref = Reference(id_gap)
            self.phase_ref = Reference(id_phase)
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, id_motor_values: Apple2Val) -> None:
        """Check ID is in a movable state and set all the demand value before moving
        them all at the same time.
        """
        gap = self.gap_ref()
        phase = self.phase_ref()
        # Only need to check gap as the phase motors share both status and gate with gap.
        await gap.raise_if_cannot_move()
        await asyncio.gather(
            phase.set_demand_positions(value=id_motor_values.extract_phase_val()),
            gap.set_demand_positions(value=float(id_motor_values.gap)),
        )
        timeout = max(await asyncio.gather(gap.get_timeout(), phase.get_timeout()))
        LOGGER.info(
            f"Moving {self.name} apple2 motors to {id_motor_values}, timeout = {timeout}"
        )
        await asyncio.gather(
            gap.set_move.set(value=1, timeout=timeout),
            phase.set_move.set(value=1, timeout=timeout),
        )
        await wait_for_value(gap.gate, UndulatorGateStatus.CLOSE, timeout=timeout)
