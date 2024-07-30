from enum import Enum

from ophyd_async.core import (
    ConfigSignal,
    DeviceVector,
    SignalR,
    StandardReadable,
)
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw


class PressureJumpCellPumpMode(str, Enum):
    MANUAL = "Manual"
    AUTO_PRESSURE = "Auto Pressure"
    AUTO_POSITION = "Auto Position"


class PressureJumpCellBusyStatus(str, Enum):
    IDLE = "Idle"
    BUSY = "Busy"


class PressureJumpCellTimerState(str, Enum):
    TIMEOUT = "TIMEOUT"
    COUNTDOWN = "COUNTDOWN"


class PressureJumpCellStopValue(str, Enum):
    CONTINUE = "CONTINUE"
    STOP = "STOP"


class PressureJumpCellValveControlRequest(str, Enum):
    OPEN = "Open"
    CLOSE = "Close"
    RESET = "Reset"
    ARM = "Arm"
    DISARM = "Disarm"


class PressureJumpCellPumpMotorControlRequest(str, Enum):
    ENABLE = "Enable"
    DISABLE = "Disable"
    RESET = "Reset"
    FORWARD = "Forward"
    REVERSE = "Reverse"


class PressureJumpCellPumpMotorDirection(str, Enum):
    ZERO = "0"
    FORWARD = "Forward"
    REVERSE = "Reverse"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"


class PressureJumpCellValveState(str, Enum):
    FAULT = "Fault"
    OPEN = "Open"
    OPENING = "Opening"
    CLOSED = "Closed"
    CLOSING = "Closing"


class PressureJumpCellFastValveState(str, Enum):
    FAULT = "Fault"
    OPEN = "Open"
    OPEN_ARMED = "Open Armed"
    CLOSED = "Closed"
    CLOSED_ARMED = "Closed Armed"
    NONE5 = "Unused"


class PressureJumpCellLimitSwitch(str, Enum):
    OFF = "Off"
    ON = "On"


class PressureJumpCellControlValves(StandardReadable):
    """
    valves 2, 4, 7, 8 are not controlled by the IOC,
    as they are under manual control.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.valve_states: DeviceVector[SignalR[PressureJumpCellValveState]] = (
                DeviceVector(
                    {
                        i: epics_signal_r(
                            PressureJumpCellValveState, f"{prefix}V{i}:STA"
                        )
                        for i in [1, 3]
                    }
                )
            )
            self.fast_valve_states: DeviceVector[
                SignalR[PressureJumpCellFastValveState]
            ] = DeviceVector(
                {
                    i: epics_signal_r(
                        PressureJumpCellFastValveState, f"{prefix}V{i}:STA"
                    )
                    for i in [5, 6]
                }
            )

        with self.add_children_as_readables(ConfigSignal):
            self.valves_open: DeviceVector[SignalR[bool]] = DeviceVector(
                {
                    i: epics_signal_rw(bool, f"{prefix}V{i}:OPENSEQ")
                    for i in [1, 3, 5, 6]
                }
            )

            self.valve_control: DeviceVector[
                SignalR[PressureJumpCellValveControlRequest]
            ] = DeviceVector(
                {
                    i: epics_signal_rw(
                        PressureJumpCellValveControlRequest, f"{prefix}V{i}:CON"
                    )
                    for i in [1, 3, 5, 6]
                }
            )

        super().__init__(name)


class PressureJumpCellPump(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.pump_position = epics_signal_r(float, prefix + "POS")
            self.pump_forward_limit = epics_signal_r(
                PressureJumpCellLimitSwitch, prefix + "D74IN1"
            )
            self.pump_backward_limit = epics_signal_r(
                PressureJumpCellLimitSwitch, prefix + "D74IN0"
            )
            self.pump_motor_direction = epics_signal_r(
                PressureJumpCellPumpMotorDirection, prefix + "MTRDIR"
            )
            self.pump_speed_rbv = epics_signal_r(int, prefix + "MSPEED_RBV")

        with self.add_children_as_readables(ConfigSignal):
            self.pump_mode = epics_signal_rw(
                PressureJumpCellPumpMode, prefix + "SP:AUTO"
            )
            self.pump_speed = epics_signal_rw(float, prefix + "MSPEED")
            self.pump_move_forward = epics_signal_rw(bool, prefix + "M1:FORW")
            self.pump_move_backward = epics_signal_rw(bool, prefix + "M1:BACKW")
            self.pump_move_backward = epics_signal_rw(
                PressureJumpCellPumpMotorControlRequest, prefix + "M1:CON"
            )

        super().__init__(name)


class PressureJumpCellPressureTransducer(StandardReadable):
    def __init__(self, prefix: str, name: str = "", adc_prefix: str = "") -> None:
        with self.add_children_as_readables():
            self.omron_pressure = epics_signal_r(float, prefix + "PP:PRES")
            self.omron_voltage = epics_signal_r(float, prefix + "PP:RAW")
            self.beckhoff_pressure = epics_signal_r(
                float, prefix + "STATP:MeanValue_RBV"
            )
            self.beckhoff_voltage = epics_signal_r(float, adc_prefix + "CH1")
            # todo this channel might be liable to change

        super().__init__(name)


class PressureJumpCellPressureTransducers(StandardReadable):
    def __init__(
        self, prefix: str, name: str = "", adc1_prefix: str = "", adc2_prefix: str = ""
    ) -> None:
        with self.add_children_as_readables():
            self.pressure_transducer_1 = PressureJumpCellPressureTransducer(
                prefix + "PP1:", name="Pressure Transducer 1", adc_prefix=adc1_prefix
            )
            self.pressure_transducer_2 = PressureJumpCellPressureTransducer(
                prefix + "PP2:", name="Pressure Transducer 2", adc_prefix=adc2_prefix
            )
            self.pressure_transducer_3 = PressureJumpCellPressureTransducer(
                prefix + "PP3:", name="Pressure Transducer 3", adc_prefix=adc1_prefix
            )

        super().__init__(name)


class PressureJumpCellController(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.control_gotobusy = epics_signal_r(
                PressureJumpCellBusyStatus, prefix + "CTRL:GOTOBUSY"
            )

            ## Control Pressure ##
            self.control_timer = epics_signal_r(
                PressureJumpCellTimerState, prefix + "CTRL:TIMER"
            )
            self.control_counter = epics_signal_r(float, prefix + "CTRL:COUNTER")
            self.control_script_status = epics_signal_r(str, prefix + "CTRL:RESULT")
            self.control_routine = epics_signal_r(str, prefix + "CTRL:METHOD")
            self.control_state = epics_signal_r(str, prefix + "CTRL:STATE")
            self.control_iteration = epics_signal_r(int, prefix + "CTRL:ITER")

        with self.add_children_as_readables(ConfigSignal):
            self.control_stop = epics_signal_rw(
                PressureJumpCellStopValue, prefix + "CTRL:STOP"
            )

            self.control_target_pressure = epics_signal_rw(
                float, prefix + "CTRL:TARGET"
            )
            self.control_timeout = epics_signal_rw(float, prefix + "CTRL:TIMER.HIGH")
            self.control_go = epics_signal_rw(bool, prefix + "CTRL:GO")

            ## Control Jump ##
            self.control_jump_from_pressure = epics_signal_rw(
                float, prefix + "CTRL:JUMPF"
            )
            self.control_jump_to_pressure = epics_signal_rw(
                float, prefix + "CTRL:JUMPT"
            )
            self.control_jump_set = epics_signal_rw(bool, prefix + "CTRL:SETJUMP")

        super().__init__(name)


class PressureJumpCell(StandardReadable):
    """
    High pressure X-ray cell, used to apply pressure or pressure jumps to a sample.
    """

    def __init__(
        self,
        prefix: str = "",
        cell_prefix: str = "",
        adc_prefix: str = "",
        name: str = "",
    ):
        cellFullPrefix = prefix + cell_prefix
        adcFullPrefix = prefix + adc_prefix

        self.valves = PressureJumpCellControlValves(cellFullPrefix, name)
        self.pump = PressureJumpCellPump(cellFullPrefix, name)
        self.transducers = PressureJumpCellPressureTransducers(
            cellFullPrefix,
            name,
            adc1_prefix=adcFullPrefix + "-01:",
            adc2_prefix=adcFullPrefix + "-02:",
        )
        self.controller = PressureJumpCellController(cellFullPrefix, name)

        with self.add_children_as_readables():
            self.cell_temperature = epics_signal_r(float, cellFullPrefix + "TEMP")

        super().__init__(name)
