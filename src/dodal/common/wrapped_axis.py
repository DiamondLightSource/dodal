import numpy as np
from ophyd_async.core import (
    Reference,
    StandardReadable,
    StandardReadableFormat,
    derived_signal_rw,
)
from ophyd_async.epics.motor import Motor

from dodal.common.maths import AngleWithPhase, MotorOffsetAndPhase


class WrappedAxis(StandardReadable):
    """This device is a wrapper around a rotational Motor that presents the unwrapped coordinate system of the
    underlying motor as a combination of a phase angle and an offset from the motor's origin coordinate.

    Attributes:
          phase (float): This is a read-write signal that corresponds to the motor's phase angle, relative to the offset.
          The behaviour of the phase signal differs from that of the underlying motor setpoint/readback signal
          in the following ways:
             * Readback values are constrained to 0 <= omega < 360
             * Write values are normalised to 0 <= omega < 360, and then mapped to the nearest unwrapped angle. The
             underlying motor will be moved via the shortest path to the required phase angle, thus the direction
             of an unwrapped axis move is not always the same as the direction of a move in the wrapped axis.
             * Write values are normalised so for un-normalised writes, the readback will differ.
             * Bluesky mvr operations greater of 180 degrees or more will not result in the expected moves.
             * Sequences of moves on the unwrapped axis that would not result in cumulative motion axis will
             result in a cumulative motion in the wrapped axis. e.g. 0 -> 120 -> 240 -> 0 is 0 degrees of real
             cumulative motion when performed in the unwrapped case, but is 360 degrees of real motion when performed
             on the wrapped axis.
             * The reverse is also true 0 -> 240 -> 360 ->  is 0 degrees of real motion when executed on the wrapped axis
              but 360 degrees when performed in the unwrapped axis.
             * The above means that use of phase to set motor position is unsuitable for axes
             where the underlying motor rotation is constrained.
          offset_and_phase (Array1D[np.float32]): retrieve the offset and phase together, for use when
             mapping to the underlying unwrapped axis. These values can be converted and manipulated using the
             AngleWithPhase helper class.
    """

    def __init__(self, real_motor: Motor, name=""):
        self._real_motor = Reference(real_motor)
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.offset_and_phase = derived_signal_rw(
                self._get_motor_offset_and_phase,
                self._set_motor_offset_and_phase,
                motor_pos=real_motor,
            )
        with self.add_children_as_readables():
            self.phase = derived_signal_rw(
                self._get_phase, self._set_phase, offset_and_phase=self.offset_and_phase
            )
        super().__init__(name=name)

    def _get_motor_offset_and_phase(self, motor_pos: float) -> MotorOffsetAndPhase:
        angle = AngleWithPhase.wrap(motor_pos)
        return np.array([angle.offset, angle.phase])

    async def _set_motor_offset_and_phase(self, value: MotorOffsetAndPhase):
        await self._real_motor().set(AngleWithPhase(value).unwrap())

    def _get_phase(self, offset_and_phase: MotorOffsetAndPhase) -> float:
        return offset_and_phase[1].item()

    async def _set_phase(self, value: float):
        """Set the motor phase to the specified phase value in degrees.
        The motor will travel via the shortest distance path.
        """
        offset_and_phase = await self.offset_and_phase.get_value()
        current_position = AngleWithPhase(offset_and_phase)
        target_value = current_position.nearest_with_phase(value).unwrap()
        await self._real_motor().set(target_value)
