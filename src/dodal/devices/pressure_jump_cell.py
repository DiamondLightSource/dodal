from enum import Enum
from ophyd_async.core import ConfigSignal, StandardReadable
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
    # TODO the nones may not be required but FVST and SXST set
    NONE1 = ""
    NONE2 = ""


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
    NONE5 = ""
    NONE6 = ""


class PressureJumpCellFastValveState(str, Enum):
    FAULT = "Fault"
    OPEN = "Open"
    OPEN_ARMED = "Open Armed"
    CLOSED = "Closed"
    CLOSED_ARMED = "Closed Armed"
    NONE5 = "Unused"
    NONE6 = ""


class PressureJumpCellLimitSwitch(str, Enum):
    OFF = "Off"
    ON = "On"


class PressureJumpCellControlValves(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.valve1_state = epics_signal_r(
                PressureJumpCellValveState, prefix + "V1:STA"
            )
            # V2 - valve manual control
            self.valve3_state = epics_signal_r(
                PressureJumpCellValveState, prefix + "V3:STA"
            )
            # V4 - valve manual control
            self.valve5_state = epics_signal_r(
                PressureJumpCellFastValveState, prefix + "V5:STA"
            )
            self.valve6_state = epics_signal_r(
                PressureJumpCellFastValveState, prefix + "V6:STA"
            )
            # V7 - valve manual control
            # V8 - valve manual control

        with self.add_children_as_readables(ConfigSignal):
            self.valve1_open = epics_signal_rw(bool, prefix + "V1:OPENSEQ")
            self.valve1_control = epics_signal_rw(
                PressureJumpCellValveControlRequest, prefix + "V1:CON"
            )

            self.valve3_open = epics_signal_rw(bool, prefix + "V3:OPENSEQ")
            self.valve3_control = epics_signal_rw(
                PressureJumpCellValveControlRequest, prefix + "V3:CON"
            )

            self.valve5_open = epics_signal_rw(bool, prefix + "V5:OPENSEQ")
            self.valve5_control = epics_signal_rw(
                PressureJumpCellValveControlRequest, prefix + "V5:CON"
            )

            self.valve6_open = epics_signal_rw(bool, prefix + "V6:OPENSEQ")
            self.valve6_control = epics_signal_rw(
                PressureJumpCellValveControlRequest, prefix + "V6CON"
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


class PressureJumpCellPressureTransducers(StandardReadable):
    def __init__(
        self, prefix: str, name: str = "", adc1_prefix: str = "", adc2_prefix: str = ""
    ) -> None:
        with self.add_children_as_readables():
            ## Pressure Transducer 1 ##
            self.pressuretransducer1_omron_pressure = epics_signal_r(
                float, prefix + "PP1:PRES"
            )
            self.pressuretransducer1_omron_voltage = epics_signal_r(
                float, prefix + "PP1:RAW"
            )
            self.pressuretransducer1_beckhoff_pressure = epics_signal_r(
                float, prefix + "STATP1:MeanValue_RBV"
            )
            self.pressuretransducer1_beckhoff_voltage = epics_signal_r(
                float, adc2_prefix + "CH1"
            )

            ## Pressure Transducer 2 ##
            self.pressuretransducer2_omron_pressure = epics_signal_r(
                float, prefix + "PP2:PRES"
            )
            self.pressuretransducer2_omron_voltage = epics_signal_r(
                float, prefix + "PP2:RAW"
            )
            self.pressuretransducer2_beckhoff_pressure = epics_signal_r(
                float, prefix + "STATP2:MeanValue_RBV"
            )
            self.pressuretransducer2_beckhoff_voltage = epics_signal_r(
                float, adc1_prefix + "CH2"
            )

            ## Pressure Transducer 3 ##
            self.pressuretransducer3_omron_pressure = epics_signal_r(
                float, prefix + "PP3:PRES"
            )
            self.pressuretransducer3_omron_voltage = epics_signal_r(
                float, prefix + "PP3:RAW"
            )
            self.pressuretransducer3_beckhoff_pressure = epics_signal_r(
                float, prefix + "STATP3:MeanValue_RBV"
            )
            self.pressuretransducer3_beckhoff_voltage = epics_signal_r(
                float, adc1_prefix + "CH1"
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
