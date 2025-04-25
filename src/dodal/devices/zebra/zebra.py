from __future__ import annotations

import asyncio
from enum import Enum
from functools import partialmethod

from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    DeviceVector,
    SignalRW,
    StandardReadable,
    StrictEnum,
    observe_value,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.devices.zebra.zebra_constants_mapping import ZebraMapping


class ArmSource(StrictEnum):
    SOFT = "Soft"
    EXTERNAL = "External"


class TrigSource(StrictEnum):
    POSITION = "Position"
    TIME = "Time"
    EXTERNAL = "External"


class EncEnum(StrictEnum):
    ENC1 = "Enc1"
    ENC2 = "Enc2"
    ENC3 = "Enc3"
    ENC4 = "Enc4"
    ENC1_4AV = "Enc1-4Av"


class I03Axes:
    SMARGON_X1 = EncEnum.ENC1
    SMARGON_Y = EncEnum.ENC2
    SMARGON_Z = EncEnum.ENC3
    OMEGA = EncEnum.ENC4


class I24Axes:
    VGON_Z = EncEnum.ENC1
    OMEGA = EncEnum.ENC2
    VGON_X = EncEnum.ENC3
    VGON_YH = EncEnum.ENC4


class I23Axes:
    OMEGA = EncEnum.ENC1


class RotationDirection(StrictEnum):
    """
    Defines for a swept angle whether the scan width (sweep) is to be added or subtracted from
    the initial angle to obtain the final angle.
    """

    POSITIVE = "Positive"
    NEGATIVE = "Negative"

    @property
    def multiplier(self):
        return 1 if self == RotationDirection.POSITIVE else -1


class ArmDemand(Enum):
    ARM = 1
    DISARM = 0


class SoftInState(StrictEnum):
    YES = "Yes"
    NO = "No"


class ArmingDevice(StandardReadable, Movable[ArmDemand]):
    """A useful device that can abstract some of the logic of arming.
    Allows a user to just call arm.set(ArmDemand.ARM)"""

    TIMEOUT: float = 3

    def __init__(self, prefix: str, name: str = "") -> None:
        self.arm_set = epics_signal_rw(float, prefix + "PC_ARM")
        self.disarm_set = epics_signal_rw(float, prefix + "PC_DISARM")
        self.armed = epics_signal_r(float, prefix + "PC_ARM_OUT")
        super().__init__(name)

    async def _set_armed(self, demand: ArmDemand):
        signal_to_set = self.arm_set if demand == ArmDemand.ARM else self.disarm_set
        await signal_to_set.set(1)
        async for reading in observe_value(self.armed):
            if reading == demand.value:
                return

    @AsyncStatus.wrap
    async def set(self, value: ArmDemand):
        await asyncio.wait_for(self._set_armed(value), timeout=self.TIMEOUT)


class PositionCompare(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.num_gates = epics_signal_rw(float, prefix + "PC_GATE_NGATE")
        self.gate_trigger = epics_signal_rw(EncEnum, prefix + "PC_ENC")
        self.gate_source = epics_signal_rw(TrigSource, prefix + "PC_GATE_SEL")
        self.gate_input = epics_signal_rw(float, prefix + "PC_GATE_INP")
        self.gate_width = epics_signal_rw(float, prefix + "PC_GATE_WID")
        self.gate_start = epics_signal_rw(float, prefix + "PC_GATE_START")
        self.gate_step = epics_signal_rw(float, prefix + "PC_GATE_STEP")

        self.pulse_source = epics_signal_rw(TrigSource, prefix + "PC_PULSE_SEL")
        self.pulse_input = epics_signal_rw(float, prefix + "PC_PULSE_INP")
        self.pulse_start = epics_signal_rw(float, prefix + "PC_PULSE_START")
        self.pulse_width = epics_signal_rw(float, prefix + "PC_PULSE_WID")
        self.pulse_step = epics_signal_rw(float, prefix + "PC_PULSE_STEP")
        self.pulse_max = epics_signal_rw(float, prefix + "PC_PULSE_MAX")

        self.dir = epics_signal_rw(RotationDirection, prefix + "PC_DIR")
        self.arm_source = epics_signal_rw(ArmSource, prefix + "PC_ARM_SEL")
        self.reset = epics_signal_rw(int, prefix + "SYS_RESET.PROC")

        self.arm = ArmingDevice(prefix)
        super().__init__(name)

    async def is_armed(self) -> bool:
        arm_state = await self.arm.armed.get_value()
        return arm_state == 1


class PulseOutput(StandardReadable):
    """Zebra pulse output panel."""

    def __init__(self, prefix: str, name: str = "") -> None:
        self.input = epics_signal_rw(float, prefix + "_INP")
        self.delay = epics_signal_rw(float, prefix + "_DLY")
        self.width = epics_signal_rw(float, prefix + "_WID")
        super().__init__(name)


class ZebraOutputPanel(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.pulse_1 = PulseOutput(prefix + "PULSE1")
        self.pulse_2 = PulseOutput(prefix + "PULSE2")

        self.out_pvs: DeviceVector[SignalRW] = DeviceVector(
            {i: epics_signal_rw(float, prefix + f"OUT{i}_TTL") for i in range(1, 5)}
        )
        super().__init__(name)


def boolean_array_to_integer(values: list[bool]) -> int:
    """Converts a boolean array to integer by interpretting it in binary with LSB 0 bit
    numbering.

    Args:
        values (List[bool]): The list of booleans to convert.

    Returns:
        int: The interpretted integer.
    """
    return sum(v << i for i, v in enumerate(values))


class GateControl(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.enable = epics_signal_rw(int, prefix + "_ENA")
        self.sources = DeviceVector(
            {i: epics_signal_rw(float, prefix + f"_INP{i}") for i in range(1, 5)}
        )
        self.invert = epics_signal_rw(int, prefix + "_INV")
        super().__init__(name)


class GateType(Enum):
    AND = "AND"
    OR = "OR"


class LogicGateConfigurer(StandardReadable):
    DEFAULT_SOURCE_IF_GATE_NOT_USED = 0

    def __init__(self, prefix: str, name: str = "") -> None:
        self.and_gates: DeviceVector[GateControl] = DeviceVector(
            {i: GateControl(prefix + f"AND{i}") for i in range(1, 5)}
        )

        self.or_gates: DeviceVector[GateControl] = DeviceVector(
            {i: GateControl(prefix + f"OR{i}") for i in range(1, 5)}
        )

        self.all_gates = {
            GateType.AND: list(self.and_gates.values()),
            GateType.OR: list(self.or_gates.values()),
        }

        super().__init__(name)

    def apply_logic_gate_config(
        self, type: GateType, gate_number: int, config: LogicGateConfiguration
    ):
        """Uses the specified `LogicGateConfiguration` to configure a gate on the Zebra.

        Args:
            type (GateType): The type of gate e.g. AND/OR
            gate_number (int): Which gate to configure.
            config (LogicGateConfiguration): A configuration for the gate.
        """
        gate: GateControl = self.all_gates[type][gate_number - 1]

        gate.enable.set(boolean_array_to_integer([True] * len(config.sources)))

        # Input Source
        for source_number, source_pv in gate.sources.items():
            try:
                source_pv.set(config.sources[source_number - 1])
            except IndexError:
                source_pv.set(self.DEFAULT_SOURCE_IF_GATE_NOT_USED)

        # Invert
        gate.invert.set(boolean_array_to_integer(config.invert))

    apply_and_gate_config = partialmethod(apply_logic_gate_config, GateType.AND)
    apply_or_gate_config = partialmethod(apply_logic_gate_config, GateType.OR)


class LogicGateConfiguration:
    NUMBER_OF_INPUTS = 4

    def __init__(self, input_source: int, invert: bool = False) -> None:
        self.sources: list[int] = []
        self.invert: list[bool] = []
        self.add_input(input_source, invert)

    def add_input(
        self, input_source: int, invert: bool = False
    ) -> LogicGateConfiguration:
        """Add an input to the gate. This will throw an assertion error if more than 4
        inputs are added to the Zebra.

        Args:
            input_source (int): The source for the input (must be between 0 and 63).
            invert (bool, optional): Whether the input should be inverted. Default
                False.

        Returns:
            LogicGateConfiguration: A description of the gate configuration.
        """
        assert len(self.sources) < 4
        assert 0 <= input_source <= 63
        self.sources.append(input_source)
        self.invert.append(invert)
        return self

    def __str__(self) -> str:
        input_strings = []
        for input, (source, invert) in enumerate(
            zip(self.sources, self.invert, strict=False)
        ):
            input_strings.append(f"INP{input + 1}={'!' if invert else ''}{source}")

        return ", ".join(input_strings)


class SoftInputs(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.soft_in_1 = epics_signal_rw(SoftInState, prefix + "SOFT_IN:B0")
        self.soft_in_2 = epics_signal_rw(SoftInState, prefix + "SOFT_IN:B1")
        self.soft_in_3 = epics_signal_rw(SoftInState, prefix + "SOFT_IN:B2")
        self.soft_in_4 = epics_signal_rw(SoftInState, prefix + "SOFT_IN:B3")
        super().__init__(name)


class Zebra(StandardReadable):
    """The Zebra device."""

    def __init__(self, mapping: ZebraMapping, name: str, prefix: str) -> None:
        self.mapping = mapping
        self.pc = PositionCompare(prefix, name)
        self.output = ZebraOutputPanel(prefix, name)
        self.inputs = SoftInputs(prefix, name)
        self.logic_gates = LogicGateConfigurer(prefix, name)
        super().__init__(name=name)
