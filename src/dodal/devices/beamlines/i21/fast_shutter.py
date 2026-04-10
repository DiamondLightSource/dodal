from typing import Generic

from ophyd_async.epics.motor import Motor

from dodal.devices.fast_shutter import EnumTypesT, FastShutter


class FastShutterWithLateralMotor(FastShutter[EnumTypesT], Generic[EnumTypesT]):
    def __init__(
        self,
        prefix: str,
        open_state: EnumTypesT,
        close_state: EnumTypesT,
        shutter_suffix: str = "CON",
        lateral_suffix: str = "LAT",
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.x = Motor(prefix + lateral_suffix)
        super().__init__(prefix + shutter_suffix, open_state, close_state, name)
