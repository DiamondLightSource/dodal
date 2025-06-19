import time
import enum
from asyncio import sleep

from ophyd_async.core import StandardReadable, observe_value, WatcherUpdate
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

ionchamber_leak_wait_time = 10.0


class GasToInject(enum.Enum):
    ARGON = "argon"
    HELIUM = "helium"
    KRYPTON = "krypton"
    NITROGEN = "nitrogen"


class IonChamberToFill(enum.Enum):
    i0 = "I0"
    i1 = "I1"
    iT = "iT"
    iRef = "iRef"


class VacuumPumpCommands(enum.Enum):
    ON = 0
    OFF = 1


class ValveCommands(enum.Enum):
    RESET = 2
    OPEN = 0
    CLOSE = 1


class PressureMode(enum.Enum):
    HOLD = 0
    PRESSURE_CONTROL = 1


class PressureController(StandardReadable):
    """
    Pressure controller for gas injection system.
    in the old system, it was called MFC1 and MFC2.
    That stood for Mass Flow Controller.
    """

    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.mode = epics_signal_rw(int, prefix + "MODE:RD")
            self.readout = epics_signal_r(float, prefix + "P:RD")
            self.setpoint = epics_signal_rw(float, prefix + "SETPOINT:WR")


class GasInjector(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.vacuum_pump = epics_signal_rw(int, prefix + "VACP1:CON")
            self.line_valve = epics_signal_rw(int, prefix + "V5:CON")
            # Gas valves as a dict
            self.gas_valves = {
                GasToInject.KRYPTON: epics_signal_rw(int, prefix + "V1:CON"),
                GasToInject.NITROGEN: epics_signal_rw(int, prefix + "V2:CON"),
                GasToInject.ARGON: epics_signal_rw(int, prefix + "V3:CON"),
                GasToInject.HELIUM: epics_signal_rw(int, prefix + "V4:CON"),
            }
            # Chamber valves as a dict
            self.chambers = {
                IonChamberToFill.i0: epics_signal_rw(int, prefix + "V6:CON"),
                IonChamberToFill.iT: epics_signal_rw(int, prefix + "V7:CON"),
                IonChamberToFill.iRef: epics_signal_rw(int, prefix + "V8:CON"),
                IonChamberToFill.i1: epics_signal_rw(int, prefix + "V9:CON"),
            }
            self.pressure_controller_1 = PressureController(
                prefix + "PCTRL1:", name="pressure_controller_1"
            )
            self.pressure_controller_2 = PressureController(
                prefix + "PCTRL2:", name="pressure_controller_2"
            )

    def get_gas_valve(self, gas: GasToInject):
        return self.gas_valves[gas]

    def get_chamber_valve(self, chamber: IonChamberToFill):
        return self.chambers[chamber]

    async def inject_gas(
        self,
        target_pressure: float,
        chamber: IonChamberToFill,
        gas: GasToInject = GasToInject.ARGON,
    ):
        chamber_valve = self.get_chamber_valve(chamber)

        gas_valve = self.get_gas_valve(gas)
        chamber_pressure = self.pressure_controller_2
        await chamber_pressure.setpoint.set(target_pressure)
        await gas_valve.set(ValveCommands.RESET.value)
        await gas_valve.set(ValveCommands.OPEN.value)
        await chamber_pressure.mode.set(PressureMode.PRESSURE_CONTROL.value)
        start = time.monotonic()
        print(f"Injecting {gas.value} into {chamber} at {target_pressure} mbar...")
        # todo check empirically if this is enough time
        async for current_pressure in observe_value(chamber_pressure.readout):
            yield WatcherUpdate(
                name="chamber_pressure",
                current=current_pressure,
                initial=target_pressure,
                target=target_pressure,
                time_elapsed=time.monotonic() - start,
            )
            if abs(current_pressure - target_pressure) < 0.1:
                break
        await chamber_valve.set(ValveCommands.CLOSE.value)
        await chamber_pressure.mode.set(PressureMode.HOLD.value)
        await gas_valve.set(ValveCommands.CLOSE.value)

    async def purge_chamber(self, chamber: IonChamberToFill):
        chamber_valve = self.get_chamber_valve(chamber)
        chamber_pressure = self.pressure_controller_2
        await self.vacuum_pump.set(VacuumPumpCommands.ON.value)
        await self.line_valve.set(ValveCommands.RESET.value)
        await self.line_valve.set(ValveCommands.OPEN.value)
        await chamber_valve.set(ValveCommands.RESET.value)
        await chamber_valve.set(ValveCommands.OPEN.value)
        base_pressure = (await chamber_pressure.readout.read())["value"]
        await chamber_valve.set(ValveCommands.CLOSE.value)

        print(f"Purging {chamber} chamber...")
        # wait for leak check
        await sleep(ionchamber_leak_wait_time)
        check_pressure = (await chamber_pressure.readout.read())["value"]
        print(
            f"Base pressure in {chamber} is {base_pressure} mbar, "
            f"check pressure after leak check is {check_pressure} mbar"
        )
        if check_pressure["value"] - base_pressure > 3:
            print(f"WARNING, suspected leak in {chamber}, stopping here!!!")

        await chamber_valve.set(ValveCommands.CLOSE.value)
        await self.line_valve.set(ValveCommands.CLOSE.value)
        await self.vacuum_pump.set(VacuumPumpCommands.OFF.value)

    async def purge_line(self):
        """
        Purge the gas-supply line.
        This is done by opening the line valve and waiting for the pressure to drop below a certain limit.
        """
        tolerance = 0.1
        await self.vacuum_pump.set(VacuumPumpCommands.ON.value)
        await self.line_valve.set(ValveCommands.RESET.value)
        await self.line_valve.set(ValveCommands.OPEN.value)
        line_pressure = (await self.pressure_controller_1.readout.read())["value"]
        LIMIT_PRESSURE = 8.5
        start = time.monotonic()
        print("Purging the gas-supply line...")

        async for current_pressure in observe_value(self.pressure_controller_1.readout):
            yield WatcherUpdate(
                name="line_pressure",
                current=current_pressure,
                initial=line_pressure,
                target=LIMIT_PRESSURE,
                time_elapsed=time.monotonic() - start,
            )
            if abs(current_pressure - LIMIT_PRESSURE) < tolerance:
                break

        await self.line_valve.set(ValveCommands.CLOSE.value)
        await self.vacuum_pump.set(VacuumPumpCommands.OFF.value)
