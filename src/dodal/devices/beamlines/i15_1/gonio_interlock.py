from math import isclose

from dodal.devices.hutch_shutter import BaseHutchInterlock

# TODO: Make this the right number
GONIO_SAFE_FOR_OPERATIONS = 65535
# GONIO_SAFE_FOR_OPERATIONS = 65439


class GonioInterlock(BaseHutchInterlock):
    """Device to check if the air is on for the goniometer air bearing."""

    def __init__(
        self,
        bl_prefix: str,
        shtr_infix: str = "",
        interlock_suffix: str = "",
        name: str = "",
    ) -> None:
        super().__init__(
            signal_type=int,
            bl_prefix=bl_prefix,
            interlock_infix=shtr_infix,
            interlock_suffix=interlock_suffix,
            name=name,
        )

    async def shutter_safe_to_operate(self) -> bool:
        """Description."""
        interlock_state = await self.status.get_value()
        return isclose(float(interlock_state), GONIO_SAFE_FOR_OPERATIONS, abs_tol=5e-2)
