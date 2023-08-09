from dataclasses import dataclass

import numpy as np
from ophyd import Component, Device, EpicsMotor


class XYZPositioner(Device):
    x: EpicsMotor = Component(EpicsMotor, "X")
    y: EpicsMotor = Component(EpicsMotor, "Y")
    z: EpicsMotor = Component(EpicsMotor, "Z")


@dataclass
class MotorLimitHelper:
    """
    Represents motor limit(s)
    """

    motor: EpicsMotor

    def is_within(self, position: float) -> bool:
        """Checks position against limits

        :param position: The position to check
        :return: True if position is within the limits
        """
        low = self.motor.low_limit_travel.get()
        high = self.motor.high_limit_travel.get()
        return low <= position <= high


@dataclass
class XYZLimitBundle:
    """
    Holder for limits reflecting an x, y, z bundle
    """

    x: MotorLimitHelper
    y: MotorLimitHelper
    z: MotorLimitHelper

    def position_valid(self, position: np.ndarray):
        if len(position) != 3:
            raise ValueError(
                f"Position valid expects a 3-vector, got {position} instead"
            )
        return (
            self.x.is_within(position[0])
            & self.y.is_within(position[1])
            & self.z.is_within(position[2])
        )
