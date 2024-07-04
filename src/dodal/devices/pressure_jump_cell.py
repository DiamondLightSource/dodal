from ophyd_async.core import ConfigSignal, StandardReadable
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw


class PressureJumpCellPumpMode:
    MANUAL = "Manual"
    AUTO_PRESSURE = "Auto Pressure"
    AUTO_POSITION = "Auto Position"


class PressureJumpCellBusyStatus:
    IDLE = "Idle"
    BUSY = "Busy"


class PressureJumpCellTimerState:
    TIMEOUT = "TIMEOUT"
    COUNTDOWN = "COUNTDOWN"


class PressureJumpCellStopValue:
    CONTINUE = "CONTINUE"
    STOP = "STOP"


class PressureJumpCell(StandardReadable):
    """
    High pressure X-ray cell, used to apply pressure or pressure jupmps to a sample.
    """

    def __init__(
        self,
        prefix: str = "",
        adc1_prefix: str = "",
        adc2_prefix: str = "",
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            ## Valves ##
            self.valve1_state = epics_signal_r(float, prefix + "V1:STA")
            # V2 - valve manual control
            self.valve3_state = epics_signal_r(float, prefix + "V3:STA")
            # V4 - valve manual control
            self.valve5_state = epics_signal_r(float, prefix + "V5:STA")
            self.valve6_state = epics_signal_r(float, prefix + "V6:STA")
            # V7 - valve manual control
            # V8 - valve manual control

            ## Cell ##
            self.cell_temperature = epics_signal_r(float, prefix + "TEMP")

            ## Pump ##
            self.pump_position = epics_signal_r(float, prefix + "POS")
            self.pump_forward_limit = epics_signal_r(float, prefix + "D74IN1")
            self.pump_backward_limit = epics_signal_r(float, prefix + "D74IN0")

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

            ##Control Common##
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
            ## Pump ##
            self.pump_mode = epics_signal_rw(
                PressureJumpCellPumpMode, prefix + "SP:AUTO"
            )

            ##Control Common##
            self.control_stop = epics_signal_rw(
                PressureJumpCellStopValue, prefix + "CTRL:STOP"
            )

            ## Control Pressure ##
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
