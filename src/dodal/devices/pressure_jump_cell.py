import asyncio
from enum import IntEnum
from typing import Generic, TypeVar

from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    DeviceVector,
    SignalR,
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

OPENSEQ_PULSE_LENGTH = 0.2


class PumpState(StrictEnum):
    MANUAL = "Manual"
    AUTO_PRESSURE = "Auto Pressure"
    AUTO_POSITION = "Auto Position"


class StopState(StrictEnum):
    CONTINUE = "CONTINUE"
    STOP = "STOP"


class ValveControlRequest(StrictEnum):
    OPEN = "Open"
    CLOSE = "Close"
    RESET = "Reset"


class FastValveControlRequest(StrictEnum):
    OPEN = ValveControlRequest.OPEN.value
    CLOSE = ValveControlRequest.CLOSE.value
    RESET = ValveControlRequest.RESET.value
    ARM = "Arm"
    DISARM = "Disarm"


class ValveOpenSeqRequest(IntEnum):
    INACTIVE = 0
    OPEN_SEQ = 1


class PumpMotorDirectionState(StrictEnum):
    EMPTY = ""
    FORWARD = "Forward"
    REVERSE = "Reverse"


class ValveState(StrictEnum):
    FAULT = "Fault"
    OPEN = "Open"
    OPENING = "Opening"
    CLOSED = "Closed"
    CLOSING = "Closing"


class FastValveState(StrictEnum):
    FAULT = ValveState.FAULT.value
    OPEN = ValveState.OPEN.value
    OPEN_ARMED = "Open Armed"
    CLOSED = ValveState.CLOSED.value
    CLOSED_ARMED = "Closed Armed"
    NONE = "Unused"


TValveControlRequest = TypeVar(
    "TValveControlRequest", bound=ValveControlRequest | FastValveControlRequest
)


class ValveControl(
    StandardReadable, Movable[TValveControlRequest], Generic[TValveControlRequest]
):
    def __init__(
        self,
        prefix: str,
        valve_control_type: type[TValveControlRequest],
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.control = epics_signal_rw(valve_control_type, prefix + ":CON")
            self.open = epics_signal_rw(int, prefix + ":OPENSEQ")
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: TValveControlRequest):
        if value.value == "Open":
            await self.open.set(ValveOpenSeqRequest.OPEN_SEQ)
            await asyncio.sleep(OPENSEQ_PULSE_LENGTH)
            await self.open.set(ValveOpenSeqRequest.INACTIVE)
        else:
            await self.control.set(value)


class AllValvesControl(StandardReadable):
    """
    The default IOC for this device only controls
    specific valves. Other valves are under manual
    control.
    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
        fast_valves_numbers: tuple[int, ...] = (5, 6),
        slow_valves_numbers: tuple[int, ...] = (1, 3),
    ) -> None:
        with self.add_children_as_readables():
            self.valve_states: DeviceVector[SignalR[ValveState]] = DeviceVector(
                {
                    i: epics_signal_r(ValveState, f"{prefix}V{i}:STA")
                    for i in slow_valves_numbers
                }
            )
            self.fast_valve_states: DeviceVector[SignalR[FastValveState]] = (
                DeviceVector(
                    {
                        i: epics_signal_r(FastValveState, f"{prefix}V{i}:STA")
                        for i in fast_valves_numbers
                    }
                )
            )

        self.fast_valve_control = {
            i: ValveControl(f"{prefix}V{i}", FastValveControlRequest)
            for i in fast_valves_numbers
        }

        self.slow_valve_control = {
            i: ValveControl(f"{prefix}V{i}", ValveControlRequest)
            for i in slow_valves_numbers
        }

        all_valves = self.fast_valve_control | self.slow_valve_control

        self.valve_control: DeviceVector[ValveControl] = DeviceVector(all_valves)

        super().__init__(name)


class Pump(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.pump_position = epics_signal_r(float, prefix + "POS")
            self.pump_motor_direction = epics_signal_r(
                PumpMotorDirectionState, prefix + "MTRDIR"
            )
            self.pump_speed = epics_signal_rw(
                float, write_pv=prefix + "MSPEED", read_pv=prefix + "MSPEED_RBV"
            )

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.pump_mode = epics_signal_rw(PumpState, prefix + "SP:AUTO")

        super().__init__(name)


class PressureTransducer(StandardReadable):
    """
    Pressure transducer for a high pressure X-ray cell.
    This is the chamber and there are three of them.
    1 is the start, 3 is where the sample is.
    NOTE: the distinction between the adc prefix and the cell prefix is kept here.

    """

    def __init__(
        self,
        prefix: str,
        cell_prefix: str,
        transducer_number: int,
        ethercat_channel_number: int,
        name: str = "",
        full_different_prefix_adc: str = "",
    ) -> None:
        final_prefix = f"{prefix}{cell_prefix}"
        with self.add_children_as_readables():
            self.omron_pressure = epics_signal_r(
                float, f"{final_prefix}PP{transducer_number}:PRES"
            )
            self.omron_voltage = epics_signal_r(
                float, f"{final_prefix}PP{transducer_number}:RAW"
            )
            self.beckhoff_pressure = epics_signal_r(
                float, f"{final_prefix}STATP{transducer_number}:MeanValue_RBV"
            )
            # P1 beckhoff voltage = BL38P-EA-ADC-02:CH1
            # P2 beckhoff voltage = BL38P-EA-ADC-01:CH2
            # P3 beckhoff voltage = BL38P-EA-ADC-01:CH1
            self.slow_beckhoff_voltage_readout = epics_signal_r(
                float, f"{full_different_prefix_adc}CH{ethercat_channel_number}"
            )

        super().__init__(name)


class PressureJumpCellController(StandardReadable):
    """
    Top-level control for a fixed pressure or pressure jumps.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.stop = epics_signal_rw(StopState, f"{prefix}STOP")

            self.target_pressure = epics_signal_rw(float, f"{prefix}TARGET")
            self.timeout = epics_signal_rw(float, f"{prefix}TIMER.HIGH")
            self.go = epics_signal_rw(bool, f"{prefix}GO")

            self.from_pressure = epics_signal_rw(float, f"{prefix}JUMPF")
            self.to_pressure = epics_signal_rw(float, f"{prefix}JUMPT")
            self.jump_ready = epics_signal_rw(bool, f"{prefix}SETJUMP")

            self.result = epics_signal_r(str, f"{prefix}RESULT")

            self._name = name
        super().__init__(name)


class PressureJumpCell(StandardReadable):
    """
    High pressure X-ray cell, used to apply pressure or pressure jumps to a sample.
    prefix: str
        The prefix of beamline - SPECIAL - unusual that the cell prefix is computed separately
    """

    def __init__(
        self,
        prefix: str,
        cell_prefix: str = "-HPXC-01:",
        adc_prefix: str = "-ADC",
        name: str = "",
    ):
        self.all_valves_control = AllValvesControl(f"{prefix}{cell_prefix}", name)
        self.pump = Pump(f"{prefix}{cell_prefix}", name)

        self.controller = PressureJumpCellController(
            f"{prefix}{cell_prefix}CTRL:", name
        )

        with self.add_children_as_readables():
            self.pressure_transducers: DeviceVector[PressureTransducer] = DeviceVector(
                {
                    1: PressureTransducer(
                        prefix=prefix,
                        cell_prefix=cell_prefix,
                        transducer_number=1,
                        full_different_prefix_adc=f"{prefix}{adc_prefix}-02:",
                        ethercat_channel_number=1,
                    ),
                    2: PressureTransducer(
                        prefix=prefix,
                        cell_prefix=cell_prefix,
                        transducer_number=2,
                        full_different_prefix_adc=f"{prefix}{adc_prefix}-01:",
                        ethercat_channel_number=2,
                    ),
                    3: PressureTransducer(
                        prefix=prefix,
                        cell_prefix=cell_prefix,
                        transducer_number=3,
                        full_different_prefix_adc=f"{prefix}{adc_prefix}-01:",
                        ethercat_channel_number=1,
                    ),
                }
            )

            self.cell_temperature = epics_signal_r(float, f"{prefix}{cell_prefix}TEMP")

        super().__init__(name)
