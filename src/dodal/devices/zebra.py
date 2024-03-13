from __future__ import annotations

from enum import Enum, IntEnum
from functools import partialmethod
from typing import List

from ophyd import StatusBase
from ophyd_async.core import SignalRW, StandardReadable
from ophyd_async.epics.signal import epics_signal_rw

from dodal.devices.status import await_value

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
PULSE2 = 53
SOFT_IN1 = 60
SOFT_IN2 = 61
SOFT_IN3 = 62

# Instrument specific
TTL_DETECTOR = 1
TTL_SHUTTER = 2
TTL_XSPRESS3 = 3
TTL_PANDA = 4


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


class FastShutterAction(IntEnum):
    OPEN = 1
    CLOSE = 0


# TODO check all types for the PVs!


class ArmingDevice(StandardReadable):
    """A useful device that can abstract some of the logic of arming.
    Allows a user to just call arm.set(ArmDemand.ARM)"""

    TIMEOUT = 3

    def __init__(self, prefix: str, name: str = "") -> None:
        self.arm_set = epics_signal_rw(int, prefix + "PC_ARM")
        self.disarm_set = epics_signal_rw(int, prefix + "PC_DISARM")
        self.armed = epics_signal_rw(int, prefix + "PC_ARM_OUT")
        super().__init__(name)

    def set(self, demand: ArmDemand) -> StatusBase:
        # TODO Ask about StatusBase vs AsyncStatus
        status = await_value(self.armed, demand.value, timeout=self.TIMEOUT)
        signal_to_set = self.arm_set if demand == ArmDemand.ARM else self.disarm_set
        status &= signal_to_set.set(1)
        return status


class PositionCompare(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.num_gates = epics_signal_rw(int, prefix + "PC_GATE_NGATE")
        self.gate_trigger = epics_signal_rw(str, prefix + "PC_ENC")
        self.gate_source = epics_signal_rw(str, prefix + "PC_GATE_SEL")
        self.gate_input = epics_signal_rw(int, prefix + "PC_GATE_INP")
        self.gate_width = epics_signal_rw(float, prefix + "PC_GATE_WID")
        self.gate_start = epics_signal_rw(float, prefix + "PC_GATE_START")
        self.gate_step = epics_signal_rw(float, prefix + "PC_GATE_STEP")

        self.pulse_source = epics_signal_rw(str, prefix + "PC_PULSE_SEL")
        self.pulse_input = epics_signal_rw(int, prefix + "PC_PULSE_INP")
        self.pulse_start = epics_signal_rw(float, prefix + "PC_PULSE_START")
        self.pulse_width = epics_signal_rw(float, prefix + "PC_PULSE_WID")
        self.pulse_step = epics_signal_rw(float, prefix + "PC_PULSE_STEP")
        self.pulse_max = epics_signal_rw(int, prefix + "PC_PULSE_MAX")

        self.dir = epics_signal_rw(int, prefix + "PC_DIR")
        self.arm_source = epics_signal_rw(str, prefix + "PC_ARM_SEL")
        self.reset = epics_signal_rw(int, prefix + "SYS_RESET.PROC")

        self.arm = ArmingDevice(prefix)
        super().__init__(name)

    async def is_armed(self) -> bool:
        # TODO Check this makes sense
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

        self.out_1 = epics_signal_rw(int, prefix + "OUT1_TTL")
        self.out_2 = epics_signal_rw(int, prefix + "OUT2_TTL")
        self.out_3 = epics_signal_rw(int, prefix + "OUT3_TTL")
        self.out_4 = epics_signal_rw(int, prefix + "OUT4_TTL")
        super().__init__(name)

    @property
    def out_pvs(self) -> List[SignalRW]:
        """A list of all the output TTL PVs. Note that as the PVs are 1 indexed
        `out_pvs[0]` is `None`.
        """
        return [None, self.out_1, self.out_2, self.out_3, self.out_4]  # type:ignore


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
    # TODO: Ophyd v1 had a timeout of 30 - see epics_signal_put_wait
    # SignalRW has
    # set(value: T, wait=True, timeout='USE_DEFAULT_TIMEOUT') → AsyncStatus
    def __init__(self, prefix: str, name: str = "") -> None:
        self.enable = epics_signal_rw(int, prefix + "_ENA")
        self.source_1 = epics_signal_rw(int, prefix + "_INP1")
        self.source_2 = epics_signal_rw(int, prefix + "_INP2")
        self.source_3 = epics_signal_rw(int, prefix + "_INP3")
        self.source_4 = epics_signal_rw(int, prefix + "_INP4")
        self.invert = epics_signal_rw(int, prefix + "_INV")
        super().__init__(name)

    @property
    def sources(self):
        return [self.source_1, self.source_2, self.source_3, self.source_4]


class GateType(Enum):
    AND = "AND"
    OR = "OR"


class LogicGateConfigurer(StandardReadable):
    DEFAULT_SOURCE_IF_GATE_NOT_USED = 0

    def __init__(self, prefix: str, name: str = "") -> None:
        self.and_gate_1 = GateControl(prefix + "AND1")
        self.and_gate_2 = GateControl(prefix + "AND2")
        self.and_gate_3 = GateControl(prefix + "AND3")
        self.and_gate_4 = GateControl(prefix + "AND4")

        self.or_gate_1 = GateControl(prefix + "OR1")
        self.or_gate_2 = GateControl(prefix + "OR1")
        self.or_gate_3 = GateControl(prefix + "OR1")
        self.or_gate_4 = GateControl(prefix + "OR1")

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
        for source_number, source_pv in enumerate(gate.sources):
            try:
                # TODO Maybe the wait can go here now?
                # What was the reason for such a long wait on the gates?
                source_pv.set(config.sources[source_number])
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
        self.soft_in_1 = epics_signal_rw(Enum, prefix + "SOFT_IN:B0")
        self.soft_in_2 = epics_signal_rw(Enum, prefix + "SOFT_IN:B1")
        self.soft_in_3 = epics_signal_rw(Enum, prefix + "SOFT_IN:B2")
        self.soft_in_4 = epics_signal_rw(Enum, prefix + "SOFT_IN:B3")
        super().__init__(name)


class Zebra(StandardReadable):
    """The Zebra device."""

    def __init__(self, name: str, prefix: str) -> None:
        self.pc = PositionCompare(prefix, name)
        self.output = ZebraOutputPanel(prefix, name)
        self.inputs = SoftInputs(prefix, name)
        self.logic_gates = LogicGateConfigurer(prefix, name)
        super().__init__(name=name)

    # pc = Component(PositionCompare, "")
    # output = Component(ZebraOutputPanel, "")
    # inputs = Component(SoftInputs, "")
    # logic_gates = Component(LogicGateConfigurer, "")
