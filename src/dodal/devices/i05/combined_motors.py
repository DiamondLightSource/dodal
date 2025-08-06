import numpy as np
from ophyd_async.core import (
    Array1D,
    StandardReadable,
)
from ophyd_async.epics.motor import Motor


class PolynomCombinedMotors(StandardReadable):
    """
    Binds two scannables, Slave against Master, via square polynom dependency
    It is a scannable in GDA sense
    There are 8 polynom parameters (4 for each slave) that one can set up (via lookuptable?)
    There is master motor and 2 slave motors
    asyncMoveTo() call seem to have a blocking sequence of moves: Master, Slave1, Slave2 - can they be moved asynchronously?
    getPosition() returns just a master motor position
    """

    def __init__(
        self,
        master_motor: Motor,
        slave_motor1: Motor,
        slave_motor2: Motor,
        slave_coeff1: Array1D[np.float64],
        slave_coeff2: Array1D[np.float64],
        name: str = "",
    ) -> None:
        # looks like this is not going to work - error can not set as child as it is already a child of pgm.
        # need to initialize all motors from PV string?
        # or make it not class but plan, function?
        self.master = master_motor
        # self.slave1 = slave_motor1
        # self.slave2 = slave_motor2

        # self.add_readables([self.master.user_readback])

        super().__init__(name=name)
