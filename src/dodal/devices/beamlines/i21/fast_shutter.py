from typing import Generic

from ophyd_async.epics.motor import Motor

from dodal.devices.fast_shutter import EnumTypesT, FastShutter


class FastShutterWithLateralMotor(FastShutter[EnumTypesT], Generic[EnumTypesT]):
    """Implementation of fast shutter that connects to an epics pv. This pv is an enum
    that controls the open and close state of the shutter.

    Args:
        pv (str): The pv to connect to the shutter device.
        open_state (EnumTypesT): The enum value that corresponds with opening the
            shutter.
        close_state (EnumTypesT): The enum value that corresponds with closing the
            shutter.
        shutter_suffix (str, optional): Shutter suffix state. Defaults to CON.
        lateral_suffix (str, optional): Lateral mottor suffix. Defaults to LAT.
        name (str, optional): The name of the shutter.
    """

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
