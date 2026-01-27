from bluesky.protocols import Pausable
from ophyd_async.core import (
    EnabledDisabled,
    StandardReadable,
    set_and_wait_for_value,
)
from ophyd_async.epics.core import epics_signal_rw


class Spinner(StandardReadable, Pausable):
    """This is a simple sample spinner, that has enable and speed (%)"""

    def __init__(
        self,
        prefix: str,
        name: str = "",
        disable_suffix: str = "SPIN:DISABLE",
        speed_suffix: str = "SPIN:SPEED",
    ):
        with self.add_children_as_readables():
            self.enable = epics_signal_rw(EnabledDisabled, prefix + disable_suffix)
            self.speed = epics_signal_rw(float, prefix + speed_suffix)

        super().__init__(name=name)

    async def pause(self):
        await set_and_wait_for_value(self.enable, EnabledDisabled.DISABLED)

    async def resume(self):
        await set_and_wait_for_value(self.enable, EnabledDisabled.ENABLED)
