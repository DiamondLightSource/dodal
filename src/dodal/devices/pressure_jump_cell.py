import asyncio
from dataclasses import dataclass
from enum import Enum

from bluesky.protocols import HasName, Movable
from ophyd_async.core import (
    AsyncStatus,
    ConfigSignal,
    DeviceVector,
    SignalR,
    SignalRW,
    StandardReadable,
)
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw


class PumpState(str, Enum):
    MANUAL = "Manual"
    AUTO_PRESSURE = "Auto Pressure"
    AUTO_POSITION = "Auto Position"


class BusyState(str, Enum):
    IDLE = "Idle"
    BUSY = "Busy"


class TimerState(str, Enum):
    TIMEOUT = "TIMEOUT"
    COUNTDOWN = "COUNTDOWN"


class StopState(str, Enum):
    CONTINUE = "CONTINUE"
    STOP = "STOP"


class FastValveControlRequest(str, Enum):
    OPEN = "Open"
    CLOSE = "Close"
    RESET = "Reset"
    ARM = "Arm"
    DISARM = "Disarm"


class ValveControlRequest(str, Enum):
    OPEN = "Open"
    CLOSE = "Close"
    RESET = "Reset"


class PumpMotorControlRequest(str, Enum):
    ENABLE = "Enable"
    DISABLE = "Disable"
    RESET = "Reset"
    FORWARD = "Forward"
    REVERSE = "Reverse"


class PumpMotorDirectionState(str, Enum):
    EMPTY = ""
    FORWARD = "Forward"
    REVERSE = "Reverse"


class ValveState(str, Enum):
    FAULT = "Fault"
    OPEN = "Open"
    OPENING = "Opening"
    CLOSED = "Closed"
    CLOSING = "Closing"


class FastValveState(str, Enum):
    FAULT = "Fault"
    OPEN = "Open"
    OPEN_ARMED = "Open Armed"
    CLOSED = "Closed"
    CLOSED_ARMED = "Closed Armed"
    NONE = "Unused"


class LimitSwitchState(str, Enum):
    OFF = "Off"
    ON = "On"


@dataclass
class AllValvesControlState:
    valve_1: ValveControlRequest | None = None
    valve_3: ValveControlRequest | None = None
    valve_5: FastValveControlRequest | None = None
    valve_6: FastValveControlRequest | None = None


class AllValvesControl(StandardReadable, Movable):
    """
    valves 2, 4, 7, 8 are not controlled by the IOC,
    as they are under manual control.
    fast_valves: tuple[int, ...] = (5, 6)
    slow_valves: tuple[int, ...] = (1, 3)
    """

    def __init__(
        self,
        prefix: str,
        name: str = "",
        fast_valves: tuple[int, ...] = (5, 6),
        slow_valves: tuple[int, ...] = (1, 3),
    ) -> None:
        self.fast_valves = fast_valves
        self.slow_valves = slow_valves
        with self.add_children_as_readables():
            self.valve_states: DeviceVector[SignalR[ValveState]] = DeviceVector(
                {
                    i: epics_signal_r(ValveState, f"{prefix}V{i}:STA")
                    for i in self.slow_valves
                }
            )
            self.fast_valve_states: DeviceVector[SignalR[FastValveState]] = (
                DeviceVector(
                    {
                        i: epics_signal_r(FastValveState, f"{prefix}V{i}:STA")
                        for i in self.fast_valves
                    }
                )
            )

        self.fast_valve_control: DeviceVector[SignalRW[FastValveControlRequest]] = (
            DeviceVector(
                {
                    i: epics_signal_rw(FastValveControlRequest, f"{prefix}V{i}:CON")
                    for i in self.fast_valves
                }
            )
        )

        self.valve_control: DeviceVector[SignalRW[ValveControlRequest]] = DeviceVector(
            {
                i: epics_signal_rw(ValveControlRequest, f"{prefix}V{i}:CON")
                for i in self.slow_valves
            }
        )

        super().__init__(name)

    async def set_valve(
        self, valve: int, value: ValveControlRequest | FastValveControlRequest
    ):
        if valve in self.slow_valves and isinstance(value, ValveControlRequest):
            await self.valve_control[valve].set(value)
        elif valve in self.fast_valves and isinstance(value, FastValveControlRequest):
            await self.fast_valve_control[valve].set(value)

    @AsyncStatus.wrap
    async def set(self, value: AllValvesControlState):
        await asyncio.gather(
            *(
                self.set_valve(int(i[-1]), value)
                for i, value in value.__dict__.items()
                if value is not None
            )
        )


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

        with self.add_children_as_readables(ConfigSignal):
            self.pump_mode = epics_signal_rw(PumpState, prefix + "SP:AUTO")

        super().__init__(name)


class PressureTransducer(StandardReadable):
    def __init__(
        self, prefix: str, number: int, name: str = "", adc_prefix: str = ""
    ) -> None:
        with self.add_children_as_readables():
            self.omron_pressure = epics_signal_r(float, f"{prefix}PP{number}:PRES")
            self.omron_voltage = epics_signal_r(float, f"{prefix}PP{number}:RAW")
            self.beckhoff_pressure = epics_signal_r(
                float, f"{prefix}STATP{number}:MeanValue_RBV"
            )
            self.beckhoff_voltage = epics_signal_r(float, adc_prefix + "CH1")

        super().__init__(name)


class PressureJumpCellController(HasName):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.stop = epics_signal_rw(StopState, f"{prefix}STOP")

        self.target_pressure = epics_signal_rw(float, f"{prefix}TARGET")
        self.timeout = epics_signal_rw(float, f"{prefix}TIMER.HIGH")
        self.go = epics_signal_rw(bool, f"{prefix}GO")

        ## Jump logic ##
        self.start_pressure = epics_signal_rw(float, f"{prefix}JUMPF")
        self.target_pressure = epics_signal_rw(float, f"{prefix}JUMPT")
        self.jump_ready = epics_signal_rw(bool, f"{prefix}SETJUMP")

        self._name = name
        super().__init__()

    @property
    def name(self):
        return self._name


class PressureJumpCell(StandardReadable):
    """
    High pressure X-ray cell, used to apply pressure or pressure jumps to a sample.
    """

    def __init__(
        self,
        beamline_prefix: str,
        prefix: str,
        cell_prefix: str = "-HPXC-01:",
        adc_prefix: str = "-ADC",
        ctrl_prefix: str = "CTRL:",
        name: str = "",
    ):
        self.all_valves_control = AllValvesControl(
            f"{beamline_prefix}{prefix}{cell_prefix}", name
        )
        self.pump = Pump(f"{beamline_prefix}{prefix}{cell_prefix}", name)

        self.controller = PressureJumpCellController(
            f"{beamline_prefix}{prefix}{cell_prefix}{ctrl_prefix}", name
        )

        with self.add_children_as_readables():
            self.pressure_transducers: DeviceVector[PressureTransducer] = DeviceVector(
                {
                    i: PressureTransducer(
                        prefix=f"{beamline_prefix}{prefix}{cell_prefix}",
                        number=i,
                        adc_prefix=f"{beamline_prefix}{adc_prefix}-0{i}:",
                    )
                    for i in [1, 2, 3]
                }
            )

            self.cell_temperature = epics_signal_r(
                float, f"{beamline_prefix}{prefix}{cell_prefix}TEMP"
            )

        super().__init__(name)
