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


class PolynomCombinedMotors(
    StandardReadable,
    Locatable[float],
    Stoppable,
):
    """
    Binds slave motors positions against master motor via polynom dependency.
    Instance of this class will be used in a scan (scannable in GDA sense).
    Moving instance of this class moves master and all slaves asynchronously.
    Locating position returns just a master motor position.
    """

    def __init__(
        self,
        master_motor: Motor,
        slaves_dict: dict[Motor, Array1D[np.float64]],
        name: str = "",
    ) -> None:
        """
        Parameters
        ----------
        master:
            Master motor
        slaves_dict:
            Dictionary of slaves motors and their polynomial coefficients
        """
        self.master = Reference(master_motor)

        self.motor_coeff_dict: dict[Reference[Motor], Array1D[np.float64]] = {}
        # master motor added with polynomial coeff (0,1)
        self.motor_coeff_dict[self.master] = np.array([0.0, 1.0])
        # slave motors added with coefficients from input parameters
        for slave in slaves_dict.keys():
            self.motor_coeff_dict[Reference(slave)] = slaves_dict[slave]

        self.add_readables(
            [ref().user_readback for ref in self.motor_coeff_dict.keys()],
            StandardReadableFormat.HINTED_SIGNAL,
        )
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, new_position: float) -> None:
        """Move master and slave motors asynchronously"""
        await asyncio.gather(
            *[
                ref().set(float(np.polynomial.polynomial.polyval(new_position, coeff)))
                for ref, coeff in self.motor_coeff_dict.items()
            ]
        )

    async def stop(self, success=False):
        """Stop all motors immediately"""
        await asyncio.gather(*[ref().stop() for ref in self.motor_coeff_dict.keys()])

    async def locate(self) -> Location[float]:
        """Return the current setpoint and readback of the MASTER motor"""
        return await self.master().locate()
