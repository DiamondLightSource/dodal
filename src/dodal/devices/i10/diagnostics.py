from enum import Enum

from ophyd_async.core import Device
from ophyd_async.epics.motor import Motor


class DiagnosticsStatge(Device):
    def __init__(
        self,
        prefix: str,
        suffix: str,
        stage_select: type[Enum],
        name: str = "",
    ) -> None:
        self.stage = Motor(prefix=prefix + suffix)
        self.select = stage_select
        super().__init__(name=name)
