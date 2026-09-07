from ophyd_async.core import StandardReadable
from ophyd_async.epics.core import epics_signal_r


class ReadOnlyWedgeAxialMotor(StandardReadable):
    """StandardReadable for a specific wedge driving axial motor.

    Args:
        prefix: The full PV name for the axial motor position read back.
        axis_label: Convenient name for identifying the wedge motor.
    """

    def __init__(self, *, prefix: str, axis_label: str) -> None:
        with self.add_children_as_readables():
            self.read_out = epics_signal_r(datatype=float, read_pv=prefix)
        super().__init__(name=f"Wedge_{axis_label}")


class ReadOnlyWheelIndexPositioner(StandardReadable):
    """StandardReadable for a specific attenuator filter wheel.

    Args:
        prefix: The full PV name for the wheel index read back.
        wheel_name: Convenient name for identifying the wheel.
    """

    def __init__(self, *, prefix: str, wheel_name: str) -> None:
        with self.add_children_as_readables():
            self.read_out = epics_signal_r(datatype=str, read_pv=prefix)
        super().__init__(name=f"Attenuator_Filter_Wheel_{wheel_name}")


class ReadOnlyAttenuatorMotorSquad:
    """Flexible readout for the entire attenuator motor set.

    Args:
        x_motor_prefix: Optional PV for reading x axis wedge motor.
        y_motor_prefix: Optional PV for reading y axis wedge motor.
        filter_wheel_1_prefix: Optional PV for reading filter wheel motor.

    Note:
    Intentionally flexible so that absence of one motor does not require a re-write.
    """

    def __init__(
        self,
        *,
        x_motor_prefix: str = "",
        y_motor_prefix: str = "",
        filter_wheel_1_prefix: str = "",
    ) -> None:

        anticipated_wedge_axes = {"x": x_motor_prefix, "y": y_motor_prefix}
        self.wedge_readouts: dict[str, StandardReadable] = {
            axis: ReadOnlyWedgeAxialMotor(prefix=motor_prefix, axis_label=axis)
            for axis, motor_prefix in anticipated_wedge_axes
            if motor_prefix
        }
        anticipated_wheel_indexers = {
            "w": filter_wheel_1_prefix,
        }
        self.wheel_readouts: dict[str, StandardReadable] = {
            label: ReadOnlyWheelIndexPositioner(prefix=indexer_prefix, wheel_name=label)
            for label, indexer_prefix in anticipated_wheel_indexers
            if indexer_prefix
        }

    async def read_wedge(self, *, axis_name) -> float:
        readable: StandardReadable = self.wedge_readouts[axis_name]
        raw_readout = await readable.read()
        return raw_readout["read_out"]["value"]

    async def read_wheel(self, *, wheel_identifier) -> int:
        readable: StandardReadable = self.wheel_readouts[wheel_identifier]
        raw_readout = await readable.read()
        return raw_readout["read_out"]["value"]

    async def read(self) -> dict[str, int | float]:
        readout: dict[str, int | float] = {}
        for axis in self.wedge_readouts:
            wedge_pos: float = await self.read_wedge(axis_name=axis)
            readout[axis] = wedge_pos
        for wheel in self.wheel_readouts:
            wheel_index: int = await self.read_wheel(wheel_identifier=wheel)
            readout[wheel] = wheel_index
        return readout
