from __future__ import annotations

import asyncio
from enum import Enum, IntEnum
from functools import partialmethod
from typing import List

from ophyd_async.core import AsyncStatus, DeviceVector, SignalRW, StandardReadable
from ophyd_async.epics.signal import epics_signal_rw

# Sources
DISCONNECT = 0
IN1_TTL = 1
IN2_TTL = 4
IN3_TTL = 7
IN4_TTL = 10
PC_ARM = 29
PC_GATE = 30
PC_PULSE = 31
AND3 = 34
AND4 = 35
OR1 = 36
PULSE1 = 52
PULSE2 = 53
SOFT_IN1 = 60
SOFT_IN2 = 61
SOFT_IN3 = 62

# Instrument specific
TTL_DETECTOR = 1
TTL_SHUTTER = 2
TTL_XSPRESS3 = 3
TTL_PANDA = 4


class ArmSource(Enum):
    SOFT = "Soft"
    EXTERNAL = "External"


class TrigSource(Enum):
    POSITION = "Position"
    TIME = "Time"
    EXTERNAL = "External"


class EncEnum(Enum):
    Enc1 = "Enc1"
    Enc2 = "Enc2"
    Enc3 = "Enc3"
    Enc4 = "Enc4"


class I03Axes(Enum):
    SMARGON_X1 = EncEnum.Enc1
    SMARGON_Y = EncEnum.Enc2
    SMARGON_Z = EncEnum.Enc3
    OMEGA = EncEnum.Enc4


class I24Axes(Enum):
    VGON_Z = EncEnum.Enc1
    OMEGA = EncEnum.Enc2
    VGON_X = EncEnum.Enc3
    VGON_YH = EncEnum.Enc4


class RotationDirection(IntEnum):
    POSITIVE = 1
    NEGATIVE = -1


class ArmDemand(IntEnum):
    ARM = 1
    DISARM = 0


class FastShutterAction(IntEnum):
    OPEN = 1
    CLOSE = 0


class SoftInState(IntEnum):
    YES = 1
    NO = 0


class ArmingDevice(StandardReadable):
    """A useful device that can abstract some of the logic of arming.
    Allows a user to just call arm.set(ArmDemand.ARM)"""

    TIMEOUT = 3

    def __init__(self, prefix: str, name: str = "") -> None:
        self.arm_set = epics_signal_rw(int, prefix + "PC_ARM")
        self.disarm_set = epics_signal_rw(int, prefix + "PC_DISARM")
        self.armed = epics_signal_rw(ArmDemand, prefix + "PC_ARM_OUT")
        super().__init__(name)

    async def _set_armed(self, demand: ArmDemand):
        await self.armed.set(demand)
        signal_to_set = self.arm_set if demand == ArmDemand.ARM else self.disarm_set
        await signal_to_set.set(1)

    def set(self, demand: ArmDemand) -> AsyncStatus:
        return AsyncStatus(
            asyncio.wait_for(self._set_armed(demand), timeout=self.TIMEOUT)
        )


class PositionCompare(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.num_gates = epics_signal_rw(int, prefix + "PC_GATE_NGATE")
        self.gate_trigger = epics_signal_rw(EncEnum, prefix + "PC_ENC")
        self.gate_source = epics_signal_rw(TrigSource, prefix + "PC_GATE_SEL")
        self.gate_input = epics_signal_rw(int, prefix + "PC_GATE_INP")
        self.gate_width = epics_signal_rw(float, prefix + "PC_GATE_WID")
        self.gate_start = epics_signal_rw(float, prefix + "PC_GATE_START")
        self.gate_step = epics_signal_rw(float, prefix + "PC_GATE_STEP")

        self.pulse_source = epics_signal_rw(TrigSource, prefix + "PC_PULSE_SEL")
        self.pulse_input = epics_signal_rw(int, prefix + "PC_PULSE_INP")
        self.pulse_start = epics_signal_rw(float, prefix + "PC_PULSE_START")
        self.pulse_width = epics_signal_rw(float, prefix + "PC_PULSE_WID")
        self.pulse_step = epics_signal_rw(float, prefix + "PC_PULSE_STEP")
        self.pulse_max = epics_signal_rw(int, prefix + "PC_PULSE_MAX")

        self.dir = epics_signal_rw(int, prefix + "PC_DIR")
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
        self.input = epics_signal_rw(int, prefix + "_INP")
        self.delay = epics_signal_rw(float, prefix + "_DLY")
        self.delay = epics_signal_rw(float, prefix + "_WID")
        super().__init__(name)


class ZebraOutputPanel(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.pulse1 = PulseOutput(prefix + "PULSE1")
        self.pulse2 = PulseOutput(prefix + "PULSE2")

        self.out_pvs: DeviceVector[SignalRW] = DeviceVector(
            {
                1: epics_signal_rw(int, prefix + "OUT1_TTL"),
                2: epics_signal_rw(int, prefix + "OUT2_TTL"),
                3: epics_signal_rw(int, prefix + "OUT3_TTL"),
                4: epics_signal_rw(int, prefix + "OUT4_TTL"),
            }
        )
        super().__init__(name)


def boolean_array_to_integer(values: List[bool]) -> int:
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
            {i: epics_signal_rw(int, prefix + f"_INP{i}") for i in range(1, 5)}
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
            {
                1: GateControl(prefix + "AND1"),
                2: GateControl(prefix + "AND2"),
                3: GateControl(prefix + "AND3"),
                4: GateControl(prefix + "AND4"),
            }
        )

        self.or_gates: DeviceVector[GateControl] = DeviceVector(
            {
                1: GateControl(prefix + "OR1"),
                2: GateControl(prefix + "OR2"),
                3: GateControl(prefix + "OR3"),
                4: GateControl(prefix + "OR4"),
            }
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
        self.sources: List[int] = []
        self.invert: List[bool] = []
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
        for input, (source, invert) in enumerate(zip(self.sources, self.invert)):
            input_strings.append(f"INP{input+1}={'!' if invert else ''}{source}")

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

    def __init__(self, name: str, prefix: str) -> None:
        self.pc = PositionCompare(prefix, name)
        self.output = ZebraOutputPanel(prefix, name)
        self.inputs = SoftInputs(prefix, name)
        self.logic_gates = LogicGateConfigurer(prefix, name)
        super().__init__(name=name)
