import abc
import asyncio
from dataclasses import dataclass
from math import isclose
from typing import Generic, Protocol, TypeVar

import numpy as np
from bluesky.protocols import Flyable, Locatable, Location, Movable, Preparable
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    AsyncStatus,
    Device,
    FlyMotorInfo,
    Reference,
    SignalR,
    SignalW,
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
    WatchableAsyncStatus,
    WatcherUpdate,
    derived_signal_rw,
    error_if_none,
    observe_value,
    soft_signal_r_and_setter,
    soft_signal_rw,
    wait_for_value,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw
from ophyd_async.epics.motor import Motor

from dodal.log import LOGGER

T = TypeVar("T")


class UndulatorGateStatus(StrictEnum):
    OPEN = "Open"
    CLOSE = "Closed"


@dataclass
class Apple2PhasesVal:
    top_outer: float
    top_inner: float
    btm_inner: float
    btm_outer: float


@dataclass
class Apple2Val(Apple2PhasesVal):
    gap: float


class Pol(StrictEnum):
    NONE = "None"
    LH = "lh"
    LV = "lv"
    PC = "pc"
    NC = "nc"
    LA = "la"
    LH3 = "lh3"


ROW_PHASE_MOTOR_TOLERANCE = 0.004
MAXIMUM_ROW_PHASE_MOTOR_POSITION = 24.0
MAXIMUM_GAP_MOTOR_POSITION = 100


async def estimate_motor_timeout(
    setpoint: SignalR, curr_pos: SignalR, velocity: SignalR
):
    vel = await velocity.get_value()
    cur_pos = await curr_pos.get_value()
    target_pos = float(await setpoint.get_value())
    return abs((target_pos - cur_pos) * 2.0 / vel) + DEFAULT_TIMEOUT


class UndulatorBase(abc.ABC, Device, Generic[T]):
    """Abstract base class for Apple2 undulator devices.

    This class provides common functionality for undulator devices, including
    gate and fault signal management, safety checks before motion, and abstract
    methods for setting demand positions and estimating move timeouts.
    """

    def __init__(self, name: str = ""):
        # Gate keeper open when move is requested, closed when move is completed
        self.gate: SignalR[UndulatorGateStatus]
        self.fault: SignalR[float]
        super().__init__(name=name)

    @abc.abstractmethod
    async def _set_demand_positions(self, value: T) -> None:
        """Set the demand positions on the device without actually hitting move."""

    @abc.abstractmethod
    async def get_timeout(self) -> float:
        """Get the timeout for the move based on an estimate of how long it will take."""

    async def raise_if_cannot_move(self) -> None:
        if await self.fault.get_value() != 0:
            raise RuntimeError(f"{self.name} is in fault state")
        if await self.gate.get_value() == UndulatorGateStatus.OPEN:
            raise RuntimeError(f"{self.name} is already in motion.")


class SafeUndulatorMover(StandardReadable, UndulatorBase, Movable[T]):
    """A device that will check it's safe to move the undulator before moving it and
    wait for the undulator to be safe again before calling the move complete.
    """

    def __init__(self, set_move: SignalW, prefix: str, name: str = ""):
        # Gate keeper open when move is requested, closed when move is completed
        self.gate = epics_signal_r(UndulatorGateStatus, prefix + "BLGATE")

        split_pv = prefix.split("-")
        fault_pv = f"{split_pv[0]}-{split_pv[1]}-STAT-{split_pv[3]}ANYFAULT"
        self.fault = epics_signal_r(float, fault_pv)
        self.set_move = set_move
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: T) -> None:
        LOGGER.info(f"Setting {self.name} to {value}")
        await self.raise_if_cannot_move()
        await self._set_demand_positions(value)
        timeout = await self.get_timeout()
        LOGGER.info(f"Moving {self.name} to {value} with timeout = {timeout}")
        await self.set_move.set(value=1, timeout=DEFAULT_TIMEOUT)
        await wait_for_value(self.gate, UndulatorGateStatus.CLOSE, timeout=timeout)


class MotorWithoutStop(Motor):
    """A motor that does not support stop."""

    def __init__(self, prefix: str, name: str = ""):
        super().__init__(prefix=prefix, name=name)
        del self.motor_stop  # Remove motor_stop from the public interface

    async def stop(self, success=False):
        LOGGER.info(f"Stopping {self.name} is not supported.")


class GapSafeUndulatorMotor(MotorWithoutStop, UndulatorBase):
    """A device that will check it's safe to move the undulator before moving it and
    wait for the undulator to be safe again before calling the move complete.
    """

    def __init__(self, set_move: SignalW[int], prefix: str, name: str = ""):
        # Gate keeper open when move is requested, closed when move is completed
        self.gate = epics_signal_r(UndulatorGateStatus, prefix + "BLGATE")

        split_pv = prefix.split("-")
        fault_pv = f"{split_pv[0]}-{split_pv[1]}-STAT-{split_pv[3]}ANYFAULT"
        self.fault = epics_signal_r(float, fault_pv)
        self.set_move = set_move
        super().__init__(prefix=prefix + "BLGAPMTR", name=name)

    @WatchableAsyncStatus.wrap
    async def set(self, new_position: float, timeout=DEFAULT_TIMEOUT):
        (
            old_position,
            units,
            precision,
        ) = await asyncio.gather(
            self.user_setpoint.get_value(),
            self.motor_egu.get_value(),
            self.precision.get_value(),
        )
        LOGGER.info(f"Setting {self.name} to {new_position}")
        await self.raise_if_cannot_move()
        await self._set_demand_positions(new_position)
        timeout = await self.get_timeout()
        LOGGER.info(f"Moving {self.name} to {new_position} with timeout = {timeout}")

        await self.set_move.set(value=1, wait=True, timeout=timeout)
        move_status = AsyncStatus(
            wait_for_value(self.gate, UndulatorGateStatus.CLOSE, timeout=timeout)
        )

        async for current_position in observe_value(
            self.user_readback, done_status=move_status
        ):
            yield WatcherUpdate(
                current=current_position,
                initial=old_position,
                target=new_position,
                name=self.name,
                unit=units,
                precision=precision,
            )


class UndulatorGap(GapSafeUndulatorMotor):
    """A device with a collection of epics signals to set Apple 2 undulator gap motion.
    Only PV used by beamline are added the full list is here:
    /dls_sw/work/R3.14.12.7/support/insertionDevice/db/IDGapVelocityControl.template
    /dls_sw/work/R3.14.12.7/support/insertionDevice/db/IDPhaseSoftMotor.template
    """

    def __init__(self, prefix: str, name: str = ""):
        """

        Parameters
        ----------
            prefix : str
                Beamline specific part of the PV
            name : str
                Name of the Id device

        """
        self.set_move = epics_signal_rw(int, prefix + "BLGSETP")
        # Nothing move until this is set to 1 and it will return to 0 when done.
        super().__init__(self.set_move, prefix, name)

        self.max_velocity = epics_signal_r(float, prefix + "BLGSETVEL.HOPR")
        self.min_velocity = epics_signal_r(float, prefix + "BLGSETVEL.LOPR")
        self.user_setpoint = epics_signal_rw(str, prefix + "BLGSET")
        """ Clear the motor config_signal as we need new PV for velocity."""
        self._describe_config_funcs = ()
        self._read_config_funcs = ()
        self.velocity = epics_signal_rw(float, prefix + "BLGSETVEL")
        self.add_readables(
            [self.velocity, self.motor_egu, self.offset],
            format=StandardReadableFormat.CONFIG_SIGNAL,
        )

    @AsyncStatus.wrap
    async def prepare(self, value: FlyMotorInfo) -> None:
        """
        Prepare for a fly scan by moving to the run-up position at max velocity.
        Stores fly info for later use in kickoff.
        """
        max_velocity, min_velocity, egu = await asyncio.gather(
            self.max_velocity.get_value(),
            self.min_velocity.get_value(),
            self.motor_egu.get_value(),
        )
        velocity = abs(value.velocity)
        if not (min_velocity <= velocity <= max_velocity):
            raise ValueError(
                f"Requested velocity {velocity} {egu}/s is out of bounds: "
                f"must be between {min_velocity} and {max_velocity} {egu}/s."
            )
        await super().prepare(value)

    async def _set_demand_positions(self, value: float) -> None:
        await self.user_setpoint.set(str(value))

    async def get_timeout(self) -> float:
        return await estimate_motor_timeout(
            self.user_setpoint, self.user_readback, self.velocity
        )


class UndulatorPhaseMotor(MotorWithoutStop):
    """A collection of epics signals for ID phase motion.
    Only PV used by beamline are added the full list is here:
    /dls_sw/work/R3.14.12.7/support/insertionDevice/db/IDPhaseSoftMotor.template
    """

    def __init__(self, prefix: str, name: str = ""):
        """
        Parameters
        ----------

        prefix : str
            The setting prefix PV.
        infix: str
            Collection of pv that are different between beamlines
        name : str
            Name of the Id phase device
        """

        motor_pv = f"{prefix}MTR"
        super().__init__(prefix=motor_pv, name=name)
        self.user_setpoint = epics_signal_rw(str, prefix + "SET")
        self.user_setpoint_readback = epics_signal_r(float, prefix + "DMD")


class UndulatorPhaseAxes(SafeUndulatorMover[Apple2PhasesVal]):
    """
    A collection of 4 phase Motor to make up the full id phase motion. We are using the diamond pv convention.
    e.g. top_outer == Q1
         top_inner == Q2
         btm_inner == q3
         btm_outer == q4

    """

    def __init__(
        self,
        prefix: str,
        top_outer: str,
        top_inner: str,
        btm_inner: str,
        btm_outer: str,
        name: str = "",
    ):
        # Gap demand set point and readback
        with self.add_children_as_readables():
            self.top_outer = UndulatorPhaseMotor(prefix=f"{prefix}BL{top_outer}")
            self.top_inner = UndulatorPhaseMotor(prefix=f"{prefix}BL{top_inner}")
            self.btm_inner = UndulatorPhaseMotor(prefix=f"{prefix}BL{btm_inner}")
            self.btm_outer = UndulatorPhaseMotor(prefix=f"{prefix}BL{btm_outer}")
        # Nothing move until this is set to 1 and it will return to 0 when done.
        self.set_move = epics_signal_rw(int, f"{prefix}BL{top_outer}" + "MOVE")

        super().__init__(self.set_move, prefix, name)

    async def _set_demand_positions(self, value: Apple2PhasesVal) -> None:
        await asyncio.gather(
            self.top_outer.user_setpoint.set(value=str(value.top_outer)),
            self.top_inner.user_setpoint.set(value=str(value.top_inner)),
            self.btm_inner.user_setpoint.set(value=str(value.btm_inner)),
            self.btm_outer.user_setpoint.set(value=str(value.btm_outer)),
        )

    async def get_timeout(self) -> float:
        """
        Get all four motor speed, current positions and target positions to calculate required timeout.
        """
        axes = [self.top_outer, self.top_inner, self.btm_inner, self.btm_outer]
        timeouts = await asyncio.gather(
            *[
                estimate_motor_timeout(
                    axis.user_setpoint_readback,
                    axis.user_readback,
                    axis.velocity,
                )
                for axis in axes
            ]
        )
        """A 2.0 multiplier is required to prevent premature motor timeouts in phase
        axes as it is a master-slave system, where the slave's movement,
        being dependent on the master, can take up to twice as long to complete.
        """
        return np.max(timeouts) * 2.0


class UndulatorJawPhase(SafeUndulatorMover[float]):
    """
    A JawPhase movable, this is use for moving the jaw phase which is use to control the
    linear arbitrary polarisation but only on some of the beamline.
    """

    def __init__(
        self,
        prefix: str,
        move_pv: str,
        jaw_phase: str = "JAW",
        name: str = "",
    ):
        # Gap demand set point and readback
        with self.add_children_as_readables():
            self.jaw_phase = UndulatorPhaseMotor(prefix=f"{prefix}BL{jaw_phase}")
        # Nothing move until this is set to 1 and it will return to 0 when done
        self.set_move = epics_signal_rw(int, f"{prefix}BL{move_pv}" + "MOVE")

        super().__init__(self.set_move, prefix, name)

    async def _set_demand_positions(self, value: float) -> None:
        await self.jaw_phase.user_setpoint.set(value=str(value))

    async def get_timeout(self) -> float:
        """
        Get motor speed, current position and target position to calculate required timeout.
        """
        return await estimate_motor_timeout(
            self.jaw_phase.user_setpoint_readback,
            self.jaw_phase.user_readback,
            self.jaw_phase.velocity,
        )


class Apple2(StandardReadable, Movable[Apple2Val]):
    """
    Device representing the combined motor controls for an Apple2 undulator.

    Attributes
    ----------
    gap : UndulatorGap
        The undulator gap motor device.
    phase : UndulatorPhaseAxes
        The undulator phase axes device, consisting of four phase motors.
    """

    def __init__(self, id_gap: UndulatorGap, id_phase: UndulatorPhaseAxes, name=""):
        """
        Parameters
        ----------

        id_gap: UndulatorGap
            An UndulatorGap device.
        id_phase: UndulatorPhaseAxes
            An UndulatorPhaseAxes device.
        name: str
            Name of the device.
        """
        with self.add_children_as_readables():
            self.gap = id_gap
            self.phase = id_phase
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, id_motor_values: Apple2Val) -> None:
        """
        Check ID is in a movable state and set all the demand value before moving them
        all at the same time.
        """

        # Only need to check gap as the phase motors share both fault and gate with gap.
        await self.gap.raise_if_cannot_move()
        await asyncio.gather(
            self.phase.top_outer.user_setpoint.set(
                value=str(id_motor_values.top_outer)
            ),
            self.phase.top_inner.user_setpoint.set(
                value=str(id_motor_values.top_inner)
            ),
            self.phase.btm_inner.user_setpoint.set(
                value=str(id_motor_values.btm_inner)
            ),
            self.phase.btm_outer.user_setpoint.set(
                value=str(id_motor_values.btm_outer)
            ),
            self.gap.user_setpoint.set(value=str(id_motor_values.gap)),
        )
        timeout = np.max(
            await asyncio.gather(self.gap.get_timeout(), self.phase.get_timeout())
        )
        LOGGER.info(
            f"Moving f{self.name} apple2 motors to {id_motor_values}, timeout = {timeout}"
        )
        await asyncio.gather(
            self.gap.set_move.set(value=1, wait=False, timeout=timeout),
            self.phase.set_move.set(value=1, wait=False, timeout=timeout),
        )
        await wait_for_value(self.gap.gate, UndulatorGateStatus.CLOSE, timeout=timeout)


class EnergyMotorConvertor(Protocol):
    def __call__(self, energy: float, pol: Pol) -> tuple[float, float]:
        """Protocol to provide energy to motor position conversion"""
        ...


Apple2Type = TypeVar("Apple2Type", bound="Apple2")


class Apple2Controller(StandardReadable, Generic[Apple2Type]):
    """

    Abstract base class for controlling an Apple2 undulator device.

    This class manages the undulator's gap and phase motors, and provides an interface
    for controlling polarisation and energy settings. It exposes derived signals for
    energy and polarisation, and handles conversion between energy/polarisation and
    motor positions via a user-supplied conversion callable.

    Attributes
    ----------
    apple2 : Reference[Apple2Type]
        Reference to the Apple2 device containing gap and phase motors.
    energy : derived_signal_rw
        Derived signal for moving and reading back energy.
    polarisation_setpoint : SignalR
        Soft signal for the polarisation setpoint.
    polarisation : derived_signal_rw
        Hardware-backed signal for polarisation readback and control.
    energy_to_motor : EnergyMotorConvertor
        Callable that converts energy and polarisation to motor positions.

    Abstract Methods
    ----------------
    _set_motors_from_energy(value: float) -> None
        Abstract method to set motor positions for a given energy and polarisation.
    energy_to_motor : EnergyMotorConvertor
        A callable that converts energy and polarisation to motor positions.

    Notes
    -----
    - Subclasses must implement `_set_motors_from_energy` for beamline-specific logic.
    - LH3 polarisation is indistinguishable from LH in hardware; special handling is provided.
    - Supports multiple polarisation modes, including linear horizontal (LH), linear vertical (LV),
      positive circular (PC), negative circular (NC), and linear arbitrary (LA).

    """

    def __init__(
        self,
        apple2: Apple2Type,
        energy_to_motor_converter: EnergyMotorConvertor,
        name: str = "",
    ) -> None:
        """

        Parameters
        ----------
        apple2: Apple2
            An Apple2 device.
        name: str
            Name of the device.
        """
        self.energy_to_motor = energy_to_motor_converter
        self.apple2 = Reference(apple2)

        # Store the set energy for readback.
        self._energy, self._energy_set = soft_signal_r_and_setter(
            float, initial_value=None, units="eV"
        )
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.energy = derived_signal_rw(
                raw_to_derived=self._read_energy,
                set_derived=self._set_energy,
                energy=self._energy,
                derived_units="eV",
            )

        # Store the polarisation for setpoint. And provide readback for LH3.
        # LH3 is a special case as it is indistinguishable from LH in the hardware.
        self.polarisation_setpoint, self._polarisation_setpoint_set = (
            soft_signal_r_and_setter(Pol)
        )
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            # Hardware backed read/write for polarisation.
            self.polarisation = derived_signal_rw(
                raw_to_derived=self._read_pol,
                set_derived=self._set_pol,
                pol=self.polarisation_setpoint,
                top_outer=self.apple2().phase.top_outer.user_readback,
                top_inner=self.apple2().phase.top_inner.user_readback,
                btm_inner=self.apple2().phase.btm_inner.user_readback,
                btm_outer=self.apple2().phase.btm_outer.user_readback,
                gap=self.apple2().gap.user_readback,
            )
        super().__init__(name)

    @abc.abstractmethod
    async def _set_motors_from_energy(self, value: float) -> None:
        """
        This method should be implemented by the beamline specific ID class as the
        motor positions will be different for each beamline depending on the
        undulator design and the lookup table used.
        """

    async def _set_energy(self, energy: float) -> None:
        await self._set_motors_from_energy(energy)
        self._energy_set(energy)

    def _read_energy(self, energy: float) -> float:
        """Readback for energy is just the set value."""
        return energy

    async def _check_and_get_pol_setpoint(self) -> Pol:
        """
        Check the polarisation setpoint and if it is NONE try to read it from
        hardware.
        """

        pol = await self.polarisation_setpoint.get_value()

        if pol == Pol.NONE:
            LOGGER.warning(
                "Found no setpoint for polarisation. Attempting to"
                " determine polarisation from hardware..."
            )
            pol = await self.polarisation.get_value()
            if pol == Pol.NONE:
                raise ValueError(
                    f"Polarisation cannot be determined from hardware for {self.name}"
                )
            self._polarisation_setpoint_set(pol)
        return pol

    async def _set_pol(
        self,
        value: Pol,
    ) -> None:
        # This changes the pol setpoint and then changes polarisation via set energy.
        self._polarisation_setpoint_set(value)
        await self.energy.set(await self.energy.get_value())

    def _read_pol(
        self,
        pol: Pol,
        top_outer: float,
        top_inner: float,
        btm_inner: float,
        btm_outer: float,
        gap: float,
    ) -> Pol:
        LOGGER.info(
            f"Reading polarisation setpoint from hardware: "
            f"top_outer={top_outer}, top_inner={top_inner}, "
            f"btm_inner={btm_inner}, btm_outer={btm_outer}, gap={gap}."
        )

        read_pol, _ = self.determine_phase_from_hardware(
            top_outer, top_inner, btm_inner, btm_outer, gap
        )
        # LH3 is indistinguishable from LH see determine_phase_from_hardware's docString
        # so we return LH3 if the setpoint is LH3 and the readback is LH.
        if pol == Pol.LH3 and read_pol == Pol.LH:
            LOGGER.info(
                "The hardware cannot distinguish between LH and LH3."
                " Returning the last commanded polarisation value"
            )
            return Pol.LH3

        return read_pol

    def determine_phase_from_hardware(
        self,
        top_outer: float,
        top_inner: float,
        btm_inner: float,
        btm_outer: float,
        gap: float,
    ) -> tuple[Pol, float]:
        """
        Determine polarisation and phase value using motor position patterns.
        However there is no way to return lh3 polarisation or higher harmonic setting.
        (May be for future one can use the inverse poly to work out the energy and try to match it with the current energy
        to workout the polarisation but during my test the inverse poly is too unstable for general use.)
        """
        if gap > MAXIMUM_GAP_MOTOR_POSITION:
            raise RuntimeError(
                f"{self.name} is not in use, close gap or set polarisation to use this ID"
            )

        if all(
            isclose(x, 0.0, abs_tol=ROW_PHASE_MOTOR_TOLERANCE)
            for x in [top_outer, top_inner, btm_inner, btm_outer]
        ):
            LOGGER.info("Determined polarisation: LH (Linear Horizontal).")
            return Pol.LH, 0.0
        if (
            isclose(
                top_outer,
                MAXIMUM_ROW_PHASE_MOTOR_POSITION,
                abs_tol=ROW_PHASE_MOTOR_TOLERANCE,
            )
            and isclose(top_inner, 0.0, abs_tol=ROW_PHASE_MOTOR_TOLERANCE)
            and isclose(
                btm_inner,
                MAXIMUM_ROW_PHASE_MOTOR_POSITION,
                abs_tol=ROW_PHASE_MOTOR_TOLERANCE,
            )
            and isclose(btm_outer, 0.0, abs_tol=ROW_PHASE_MOTOR_TOLERANCE)
        ):
            LOGGER.info("Determined polarisation: LV (Linear Vertical).")
            return Pol.LV, MAXIMUM_ROW_PHASE_MOTOR_POSITION
        if (
            isclose(top_outer, btm_inner, abs_tol=ROW_PHASE_MOTOR_TOLERANCE)
            and top_outer > 0.0
            and isclose(top_inner, 0.0, abs_tol=ROW_PHASE_MOTOR_TOLERANCE)
            and isclose(btm_outer, 0.0, abs_tol=ROW_PHASE_MOTOR_TOLERANCE)
        ):
            LOGGER.info("Determined polarisation: PC (Positive Circular).")
            return Pol.PC, top_outer
        if (
            isclose(top_outer, btm_inner, abs_tol=ROW_PHASE_MOTOR_TOLERANCE)
            and top_outer < 0.0
            and isclose(top_inner, 0.0, abs_tol=ROW_PHASE_MOTOR_TOLERANCE)
            and isclose(btm_outer, 0.0, abs_tol=ROW_PHASE_MOTOR_TOLERANCE)
        ):
            LOGGER.info("Determined polarisation: NC (Negative Circular).")
            return Pol.NC, top_outer
        if (
            isclose(top_outer, -btm_inner, abs_tol=ROW_PHASE_MOTOR_TOLERANCE)
            and isclose(top_inner, 0.0, abs_tol=ROW_PHASE_MOTOR_TOLERANCE)
            and isclose(btm_outer, 0.0, abs_tol=ROW_PHASE_MOTOR_TOLERANCE)
        ):
            LOGGER.info("Determined polarisation: LA (Positive Linear Arbitrary).")
            return Pol.LA, top_outer
        if (
            isclose(top_inner, -btm_outer, abs_tol=ROW_PHASE_MOTOR_TOLERANCE)
            and isclose(top_outer, 0.0, abs_tol=ROW_PHASE_MOTOR_TOLERANCE)
            and isclose(btm_inner, 0.0, abs_tol=ROW_PHASE_MOTOR_TOLERANCE)
        ):
            LOGGER.info("Determined polarisation: LA (Negative Linear Arbitrary).")
            return Pol.LA, top_inner

        LOGGER.warning("Unable to determine polarisation. Defaulting to NONE.")
        return Pol.NONE, 0.0


class InsertionDeviceEnergy(StandardReadable, Movable[float], Preparable, Flyable):
    """Apple2 ID energy movable device."""

    def __init__(
        self, id_controller: Apple2Controller[Apple2Type], name: str = ""
    ) -> None:
        self.energy = Reference(id_controller.energy)
        self._id_controller = Reference(id_controller)
        super().__init__(name=name)

        self.add_readables(
            [
                self.energy(),
            ],
            StandardReadableFormat.HINTED_SIGNAL,
        )

    @AsyncStatus.wrap
    async def set(self, energy: float) -> None:
        await self.energy().set(energy)

    @AsyncStatus.wrap
    async def prepare(self, value: FlyMotorInfo) -> None:
        """Convert FlyMotorInfo from energy to gap motion and move phase motor to mid point."""
        mid_energy = (value.start_position + value.end_position) / 2.0
        LOGGER.info(
            f"Preparing for fly energy scan, move {self._id_controller().apple2().phase} to {mid_energy}"
        )
        await self.set(energy=mid_energy)
        current_pol = await self._id_controller().polarisation_setpoint.get_value()
        start_position = self._id_controller().energy_to_motor(
            energy=value.start_position,
            pol=current_pol,
        )
        end_position = self._id_controller().energy_to_motor(
            energy=value.end_position, pol=current_pol
        )

        gap_fly_motor_info = FlyMotorInfo(
            start_position=start_position[0],
            end_position=end_position[0],
            time_for_move=value.time_for_move,
        )
        LOGGER.info(
            f"Flyscan info in energy: {value}"
            + f"Flyscan info in gap: {gap_fly_motor_info}"
        )

        await self._id_controller().apple2().gap.prepare(value=gap_fly_motor_info)

    @AsyncStatus.wrap
    async def kickoff(self):
        await self._id_controller().apple2().gap.kickoff()

    def complete(self) -> WatchableAsyncStatus:
        return self._id_controller().apple2().gap.complete()

    async def get_id_acceleration_time(self) -> float:
        return await self._id_controller().apple2().gap.acceleration_time.get_value()


class BeamEnergy(StandardReadable, Movable[float], Preparable, Flyable):
    """
    Compound device to set both ID and energy motor at the same time with an option to add an offset.
    """

    def __init__(
        self, id_energy: InsertionDeviceEnergy, mono: Motor, name: str = ""
    ) -> None:
        """
        Parameters
        ----------

        id_energy: InsertionDeviceEnergy
            An InsertionDeviceEnergy device.
        mono: Motor
            A Motor(energy) device.
        name:
            New device name.
        """
        super().__init__(name=name)
        self._id_energy = Reference(id_energy)
        self._mono_energy = Reference(mono)

        self.add_readables(
            [
                self._id_energy().energy(),
                self._mono_energy().user_readback,
            ],
            StandardReadableFormat.HINTED_SIGNAL,
        )

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.id_energy_offset = soft_signal_rw(float, initial_value=0)

    @AsyncStatus.wrap
    async def set(self, energy: float) -> None:
        LOGGER.info(f"Moving f{self.name} energy to {energy}.")
        await asyncio.gather(
            self._id_energy().set(
                energy=energy + await self.id_energy_offset.get_value()
            ),
            self._mono_energy().set(energy),
        )

    @AsyncStatus.wrap
    async def prepare(self, value: FlyMotorInfo) -> None:
        await asyncio.gather(
            self._id_energy().prepare(value), self._mono_energy().prepare(value)
        )

    @AsyncStatus.wrap
    async def kickoff(self):
        pgm_acceleration_time, gap_acceleration_time = await asyncio.gather(
            self._mono_energy().acceleration_time.get_value(),
            self._id_energy().get_id_acceleration_time(),
        )
        start_offset_time = pgm_acceleration_time - gap_acceleration_time

        await self._mono_energy().kickoff()
        await asyncio.sleep(start_offset_time)
        await self._id_energy().kickoff()
        self._fly_status = self._combined_fly_status()

    def complete(self) -> AsyncStatus:
        """Stop when both pgm and id is done moving."""
        fly_status = error_if_none(self._fly_status, "kickoff not called")
        return fly_status

    @AsyncStatus.wrap
    async def _combined_fly_status(self):
        status_pgm = self._mono_energy().complete()
        status_id = self._id_energy().complete()
        await asyncio.gather(status_pgm, status_id)


class InsertionDevicePolarisation(StandardReadable, Locatable[Pol]):
    """Apple2 ID polarisation movable device."""

    def __init__(self, id_controller: Apple2Controller, name: str = "") -> None:
        self.polarisation = Reference(id_controller.polarisation)
        self.polarisation_setpoint = Reference(id_controller.polarisation_setpoint)
        super().__init__(name=name)

        self.add_readables([self.polarisation()], StandardReadableFormat.HINTED_SIGNAL)

    @AsyncStatus.wrap
    async def set(self, pol: Pol) -> None:
        await self.polarisation().set(pol)

    async def locate(self) -> Location[Pol]:
        """Return the current polarisation"""
        setpoint, readback = await asyncio.gather(
            self.polarisation_setpoint().get_value(), self.polarisation().get_value()
        )
        return Location(setpoint=setpoint, readback=readback)
