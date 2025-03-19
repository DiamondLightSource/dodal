import asyncio
from dataclasses import dataclass

from bluesky.protocols import HasName, Movable
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


class FastValveControlRequest(StrictEnum):
    OPEN = "Open"
    CLOSE = "Close"
    RESET = "Reset"
    ARM = "Arm"
    DISARM = "Disarm"


class ValveControlRequest(StrictEnum):
    OPEN = "Open"
    CLOSE = "Close"
    RESET = "Reset"


class ValveOpenSeqRequest(StrictEnum):
    INACTIVE = "0"
    OPEN_SEQ = "1"


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
    FAULT = "Fault"
    OPEN = "Open"
    OPEN_ARMED = "Open Armed"
    CLOSED = "Closed"
    CLOSED_ARMED = "Closed Armed"
    NONE = "Unused"


@dataclass
class AllValvesControlState:
    valve_1: ValveControlRequest | None = None
    valve_3: ValveControlRequest | None = None
    valve_5: FastValveControlRequest | None = None
    valve_6: FastValveControlRequest | None = None


class AllValvesControl(StandardReadable, Movable[AllValvesControlState]):
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

        self.fast_valve_control: DeviceVector[FastValveControl] = DeviceVector(
            {i: FastValveControl(f"{prefix}V{i}") for i in self.fast_valves}
        )

        self.valve_control: DeviceVector[ValveControl] = DeviceVector(
            {i: ValveControl(f"{prefix}V{i}") for i in self.slow_valves}
        )

        super().__init__(name)

    async def set_valve(
        self,
        valve: int,
        value: ValveControlRequest | FastValveControlRequest,
    ):
        if valve in self.slow_valves and (isinstance(value, ValveControlRequest)):
            if value == ValveControlRequest.OPEN:
                await self.valve_control[valve].set(ValveOpenSeqRequest.OPEN_SEQ)
                await asyncio.sleep(OPENSEQ_PULSE_LENGTH)
                await self.valve_control[valve].set(ValveOpenSeqRequest.INACTIVE)
            else:
                await self.valve_control[valve].set(value)

        elif valve in self.fast_valves and (isinstance(value, FastValveControlRequest)):
            if value == FastValveControlRequest.OPEN:
                await self.fast_valve_control[valve].set(ValveOpenSeqRequest.OPEN_SEQ)
                await asyncio.sleep(OPENSEQ_PULSE_LENGTH)
                await self.fast_valve_control[valve].set(ValveOpenSeqRequest.INACTIVE)
            else:
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


class ValveControl(
    StandardReadable, Movable[ValveControlRequest | ValveOpenSeqRequest]
):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.close = epics_signal_rw(ValveControlRequest, prefix + ":CON")
            self.open = epics_signal_rw(int, prefix + ":OPENSEQ")

        super().__init__(name)

    def set(self, value: ValveControlRequest | ValveOpenSeqRequest) -> AsyncStatus:
        set_status = None

        if isinstance(value, ValveControlRequest):
            set_status = self.close.set(value)
        elif isinstance(value, ValveOpenSeqRequest):
            set_status = self.open.set(value.value)

        return set_status


class FastValveControl(
    StandardReadable, Movable[FastValveControlRequest | ValveOpenSeqRequest]
):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.close = epics_signal_rw(FastValveControlRequest, prefix + ":CON")
            self.open = epics_signal_rw(int, prefix + ":OPENSEQ")

        super().__init__(name)

    def set(self, value: FastValveControlRequest | ValveOpenSeqRequest) -> AsyncStatus:
        set_status = None

        if isinstance(value, FastValveControlRequest):
            set_status = self.close.set(value)
        elif isinstance(value, ValveOpenSeqRequest):
            set_status = self.open.set(value.value)

        return set_status


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
