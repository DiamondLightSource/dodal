import asyncio

import numpy as np
from bluesky.protocols import (
    Locatable,
    Location,
    Movable,
    Stoppable,
)
from ophyd_async.core import (
    Array1D,
    AsyncStatus,
    Reference,
    StandardReadable,
    StandardReadableFormat,
)
from ophyd_async.epics.motor import Motor


class PolynomCombinedMotors(
    StandardReadable,
    Locatable[float],
    Movable,
    Stoppable,
):
    """
    Binds two scannables, Slave against Master, via square polynom dependency.
    It is a scannable in GDA sense.
    There are 8 polynom parameters (4 for each slave) that one can set up (via lookuptable?)
    There is master motor and 2 slave motors.
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
        self.slave_coeff_1 = slave_coeff1
        self.slave_coeff_2 = slave_coeff2
        self.master = Reference(master_motor)
        self.slave1 = Reference(slave_motor1)
        self.slave2 = Reference(slave_motor2)

        self.add_readables(
            [
                self.master().user_readback,
                self.slave1().user_readback,
                self.slave2().user_readback,
            ],
            StandardReadableFormat.HINTED_SIGNAL,
        )

        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, new_position: float) -> None:
        """Move master and slave motors asynchronously"""
        await asyncio.gather(
            self.master().set(new_position),
            self.slave1().set(
                float(
                    np.polynomial.polynomial.polyval(new_position, self.slave_coeff_1)
                )
            ),
            self.slave2().set(
                float(
                    np.polynomial.polynomial.polyval(new_position, self.slave_coeff_2)
                )
            ),
        )

    async def stop(self, success=False):
        """Stop all motors immediately"""
        await asyncio.gather(
            self.master().stop(),
            self.slave1().stop(),
            self.slave2().stop(),
        )

    async def locate(self) -> Location[float]:
        """Return the current setpoint and readback of the MASTER motor"""
        return await self.master().locate()
