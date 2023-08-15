from __future__ import annotations

from enum import Enum, IntEnum
from functools import partialmethod
from typing import List

from ophyd import Component, Device, EpicsSignal, StatusBase

from dodal.devices.status import await_value
from dodal.devices.utils import epics_signal_put_wait

PC_ARM_SOURCE_SOFT = "Soft"
PC_ARM_SOURCE_EXT = "External"

PC_GATE_SOURCE_POSITION = 0
PC_GATE_SOURCE_TIME = 1
PC_GATE_SOURCE_EXTERNAL = 2

PC_PULSE_SOURCE_POSITION = 0
PC_PULSE_SOURCE_TIME = 1
PC_PULSE_SOURCE_EXTERNAL = 2

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
SOFT_IN3 = 62

# Instrument specific
TTL_DETECTOR = 1
TTL_SHUTTER = 2
TTL_XSPRESS3 = 3


class I03Axes(Enum):
    SMARGON_X1 = "Enc1"
    SMARGON_Y = "Enc2"
    SMARGON_Z = "Enc3"
    OMEGA = "Enc4"


class I24Axes(Enum):
    VGON_Z = "Enc1"
    OMEGA = "Enc2"
    VGON_X = "Enc3"
    VGON_YH = "Enc4"


class RotationDirection(IntEnum):
    POSITIVE = 1
    NEGATIVE = -1


class ArmDemand(IntEnum):
    ARM = 1
    DISARM = 0


class ArmingDevice(Device):
    """A useful device that can abstract some of the logic of arming.
    Allows a user to just call arm.set(ArmDemand.ARM)"""

    TIMEOUT = 3

    arm_set: EpicsSignal = Component(EpicsSignal, "PC_ARM")
    disarm_set: EpicsSignal = Component(EpicsSignal, "PC_DISARM")
    armed: EpicsSignal = Component(EpicsSignal, "PC_ARM_OUT")

    def set(self, demand: ArmDemand) -> StatusBase:
        status = await_value(self.armed, demand.value, timeout=self.TIMEOUT)
        signal_to_set = self.arm_set if demand == ArmDemand.ARM else self.disarm_set
        status &= signal_to_set.set(1)
        return status


class PositionCompare(Device):
    num_gates: EpicsSignal = epics_signal_put_wait("PC_GATE_NGATE")
    gate_trigger: EpicsSignal = epics_signal_put_wait("PC_ENC")
    gate_source: EpicsSignal = epics_signal_put_wait("PC_GATE_SEL")
    gate_input: EpicsSignal = epics_signal_put_wait("PC_GATE_INP")
    gate_width: EpicsSignal = epics_signal_put_wait("PC_GATE_WID")
    gate_start: EpicsSignal = epics_signal_put_wait("PC_GATE_START")

    pulse_source: EpicsSignal = epics_signal_put_wait("PC_PULSE_SEL")
    pulse_input: EpicsSignal = epics_signal_put_wait("PC_PULSE_INP")
    pulse_start: EpicsSignal = epics_signal_put_wait("PC_PULSE_START")
    pulse_width: EpicsSignal = epics_signal_put_wait("PC_PULSE_WID")
    pulse_step: EpicsSignal = epics_signal_put_wait("PC_PULSE_STEP")

    dir: EpicsSignal = Component(EpicsSignal, "PC_DIR")
    arm_source: EpicsSignal = epics_signal_put_wait("PC_ARM_SEL")
    reset: EpicsSignal = Component(EpicsSignal, "SYS_RESET.PROC")

    arm: ArmingDevice = Component(ArmingDevice, "")

    def is_armed(self) -> bool:
        return self.arm.armed.get() == 1


class ZebraOutputPanel(Device):
    pulse_1_input: EpicsSignal = epics_signal_put_wait("PULSE1_INP")

    out_1: EpicsSignal = epics_signal_put_wait("OUT1_TTL")
    out_2: EpicsSignal = epics_signal_put_wait("OUT2_TTL")
    out_3: EpicsSignal = epics_signal_put_wait("OUT3_TTL")
    out_4: EpicsSignal = epics_signal_put_wait("OUT4_TTL")

    @property
    def out_pvs(self) -> List[EpicsSignal]:
        """A list of all the output TTL PVs. Note that as the PVs are 1 indexed
        `out_pvs[0]` is `None`.
        """
        return [None, self.out_1, self.out_2, self.out_3, self.out_4]


def boolean_array_to_integer(values: List[bool]) -> int:
    """Converts a boolean array to integer by interpretting it in binary with LSB 0 bit
    numbering.

    Args:
        values (List[bool]): The list of booleans to convert.

    Returns:
        int: The interpretted integer.
    """
    return sum(v << i for i, v in enumerate(values))


class GateControl(Device):
    enable: EpicsSignal = epics_signal_put_wait("_ENA", 30.0)
    source_1: EpicsSignal = epics_signal_put_wait("_INP1", 30.0)
    source_2: EpicsSignal = epics_signal_put_wait("_INP2", 30.0)
    source_3: EpicsSignal = epics_signal_put_wait("_INP3", 30.0)
    source_4: EpicsSignal = epics_signal_put_wait("_INP4", 30.0)
    invert: EpicsSignal = epics_signal_put_wait("_INV", 30.0)

    @property
    def sources(self):
        return [self.source_1, self.source_2, self.source_3, self.source_4]


class GateType(Enum):
    AND = "AND"
    OR = "OR"


class LogicGateConfigurer(Device):
    DEFAULT_SOURCE_IF_GATE_NOT_USED = 0

    and_gate_1 = Component(GateControl, "AND1")
    and_gate_2 = Component(GateControl, "AND2")
    and_gate_3 = Component(GateControl, "AND3")
    and_gate_4 = Component(GateControl, "AND4")

    or_gate_1 = Component(GateControl, "OR1")
    or_gate_2 = Component(GateControl, "OR2")
    or_gate_3 = Component(GateControl, "OR3")
    or_gate_4 = Component(GateControl, "OR4")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.all_gates = {
            GateType.AND: [
                self.and_gate_1,
                self.and_gate_2,
                self.and_gate_3,
                self.and_gate_4,
            ],
            GateType.OR: [
                self.or_gate_1,
                self.or_gate_2,
                self.or_gate_3,
                self.or_gate_4,
            ],
        }

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

        gate.enable.put(boolean_array_to_integer([True] * len(config.sources)))

        # Input Source
        for source_number, source_pv in enumerate(gate.sources):
            try:
                source_pv.put(config.sources[source_number])
            except IndexError:
                source_pv.put(self.DEFAULT_SOURCE_IF_GATE_NOT_USED)

        # Invert
        gate.invert.put(boolean_array_to_integer(config.invert))

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


class SoftInputs(Device):
    soft_in_1: EpicsSignal = Component(EpicsSignal, "SOFT_IN:B0")
    soft_in_2: EpicsSignal = Component(EpicsSignal, "SOFT_IN:B1")
    soft_in_3: EpicsSignal = Component(EpicsSignal, "SOFT_IN:B2")
    soft_in_4: EpicsSignal = Component(EpicsSignal, "SOFT_IN:B3")


class Zebra(Device):
    pc: PositionCompare = Component(PositionCompare, "")
    output: ZebraOutputPanel = Component(ZebraOutputPanel, "")
    inputs: SoftInputs = Component(SoftInputs, "")
    logic_gates: LogicGateConfigurer = Component(LogicGateConfigurer, "")
