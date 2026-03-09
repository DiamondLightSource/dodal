import asyncio

import numpy as np
from bluesky.protocols import (
    Locatable,
    Location,
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


class PolynomCompoundMotors(
    StandardReadable,
    Locatable[float],
    Stoppable,
):
    """Compound motor controller that synchronizes the movement of multiple motors
    based on polynomial relationships.

    When the master motor is moved, all driven (slave) motors are asynchronously moved
    to positions calculated using polynomial coefficients from master motor position.
    The master motor is always included with a default polynomial coefficient
    of [0.0, 1.0], representing a direct mapping. Driven motors' positions are
    calculated using NumPy's polynomial evaluation.

    Args:
        master(Motor): master motor.
        driven_dict (dict[Motor, Array1D[np.float64]]): dictionary that defines mapping
            of each driven motor to its polynomial coefficients (NumPy array).
        name (str,optional): name of the device. Defaults to an empty string.
    """

    def __init__(
        self,
        master: Motor,
        driven_dict: dict[Motor, Array1D[np.float64]],
        name: str = "",
    ) -> None:
        self.motor_coeff_dict: dict[Reference[Motor], Array1D[np.float64]] = {}

        # master motor added with polynomial coeff (0,1)
        self.master_ref = Reference(master)
        self.motor_coeff_dict[self.master_ref] = np.array([0.0, 1.0])

        # slave motors added with coefficients from input parameters
        for slave in driven_dict.keys():
            self.motor_coeff_dict[Reference(slave)] = driven_dict[slave]

        self.add_readables(
            [ref().user_readback for ref in self.motor_coeff_dict.keys()],
            StandardReadableFormat.HINTED_SIGNAL,
        )
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, new_position: float) -> None:
        await asyncio.gather(
            *[
                ref().set(float(np.polynomial.polynomial.polyval(new_position, coeff)))
                for ref, coeff in self.motor_coeff_dict.items()
            ]
        )

    async def stop(self, success=False):
        await asyncio.gather(*[ref().stop() for ref in self.motor_coeff_dict.keys()])

    async def locate(self) -> Location[float]:
        return await self.master_ref().locate()
