import abc
import asyncio
from dataclasses import dataclass
from math import isclose
from typing import Generic, Protocol, TypeVar

import numpy as np
from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    SignalR,
    SignalW,
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
    derived_signal_rw,
    soft_signal_r_and_setter,
    wait_for_value,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_w

from dodal.log import LOGGER

T = TypeVar("T")

DEFAULT_MOTOR_MIN_TIMEOUT = 10


class UndulatorGateStatus(StrictEnum):
    OPEN = "Open"
    CLOSE = "Closed"


@dataclass
class Apple2PhasesVal:
    top_outer: str
    top_inner: str
    btm_inner: str
    btm_outer: str


@dataclass
class Apple2Val:
    gap: str
    top_outer: str
    top_inner: str
    btm_inner: str
    btm_outer: str


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
    return abs((target_pos - cur_pos) * 2.0 / vel) + DEFAULT_MOTOR_MIN_TIMEOUT


class SafeUndulatorMover(StandardReadable, Movable[T], Generic[T]):
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
        await self.set_move.set(value=1, timeout=timeout)
        await wait_for_value(self.gate, UndulatorGateStatus.CLOSE, timeout=timeout)

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


class UndulatorGap(SafeUndulatorMover[float]):
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

        # Gap demand set point and readback
        self.user_setpoint = epics_signal_rw(
            str, prefix + "GAPSET.B", prefix + "BLGSET"
        )
        # Nothing move until this is set to 1 and it will return to 0 when done
        self.set_move = epics_signal_rw(int, prefix + "BLGSETP")

        # These are gap velocity limit.
        self.max_velocity = epics_signal_r(float, prefix + "BLGSETVEL.HOPR")
        self.min_velocity = epics_signal_r(float, prefix + "BLGSETVEL.LOPR")
        # These are gap limit.
        self.high_limit_travel = epics_signal_r(float, prefix + "BLGAPMTR.HLM")
        self.low_limit_travel = epics_signal_r(float, prefix + "BLGAPMTR.LLM")

        # This is calculated acceleration from speed
        self.acceleration_time = epics_signal_r(float, prefix + "IDGSETACC")

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            # Unit
            self.motor_egu = epics_signal_r(str, prefix + "BLGAPMTR.EGU")
            # Gap velocity
            self.velocity = epics_signal_rw(float, prefix + "BLGSETVEL")
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            # Gap readback value
            self.user_readback = epics_signal_r(float, prefix + "CURRGAPD")
        super().__init__(self.set_move, prefix, name)

    async def _set_demand_positions(self, value: float) -> None:
        await self.user_setpoint.set(str(value))

    async def get_timeout(self) -> float:
        return await estimate_motor_timeout(
            self.user_setpoint, self.user_readback, self.velocity
        )


class UndulatorPhaseMotor(StandardReadable):
    """A collection of epics signals for ID phase motion.
    Only PV used by beamline are added the full list is here:
    /dls_sw/work/R3.14.12.7/support/insertionDevice/db/IDPhaseSoftMotor.template
    """

    def __init__(self, prefix: str, infix: str, name: str = ""):
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
        fullPV = f"{prefix}BL{infix}"
        self.user_setpoint = epics_signal_w(str, fullPV + "SET")
        self.user_setpoint_readback = epics_signal_r(float, fullPV + "DMD")
        fullPV = fullPV + "MTR"
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.user_readback = epics_signal_r(float, fullPV + ".RBV")

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.motor_egu = epics_signal_r(str, fullPV + ".EGU")
            self.velocity = epics_signal_rw(float, fullPV + ".VELO")

        self.max_velocity = epics_signal_r(float, fullPV + ".VMAX")
        self.acceleration_time = epics_signal_rw(float, fullPV + ".ACCL")
        self.precision = epics_signal_r(int, fullPV + ".PREC")
        self.deadband = epics_signal_r(float, fullPV + ".RDBD")
        self.motor_done_move = epics_signal_r(int, fullPV + ".DMOV")
        self.low_limit_travel = epics_signal_rw(float, fullPV + ".LLM")
        self.high_limit_travel = epics_signal_rw(float, fullPV + ".HLM")
        super().__init__(name=name)


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
            self.top_outer = UndulatorPhaseMotor(prefix=prefix, infix=top_outer)
            self.top_inner = UndulatorPhaseMotor(prefix=prefix, infix=top_inner)
            self.btm_inner = UndulatorPhaseMotor(prefix=prefix, infix=btm_inner)
            self.btm_outer = UndulatorPhaseMotor(prefix=prefix, infix=btm_outer)
        # Nothing move until this is set to 1 and it will return to 0 when done.
        self.set_move = epics_signal_rw(int, f"{prefix}BL{top_outer}" + "MOVE")

        super().__init__(self.set_move, prefix, name)

    async def _set_demand_positions(self, value: Apple2PhasesVal) -> None:
        await asyncio.gather(
            self.top_outer.user_setpoint.set(value=value.top_outer),
            self.top_inner.user_setpoint.set(value=value.top_inner),
            self.btm_inner.user_setpoint.set(value=value.btm_inner),
            self.btm_outer.user_setpoint.set(value=value.btm_outer),
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
            self.jaw_phase = UndulatorPhaseMotor(prefix=prefix, infix=jaw_phase)
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


class Apple2Motors(StandardReadable, Movable):
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
        all at the same time. This should be modified by the beamline specific ID
        class, if the ID motors has to move in a specific order.
        """

        # Only need to check gap as the phase motors share both fault and gate with gap.
        await self.gap.raise_if_cannot_move()
        await asyncio.gather(
            self.phase.top_outer.user_setpoint.set(value=id_motor_values.top_outer),
            self.phase.top_inner.user_setpoint.set(value=id_motor_values.top_inner),
            self.phase.btm_inner.user_setpoint.set(value=id_motor_values.btm_inner),
            self.phase.btm_outer.user_setpoint.set(value=id_motor_values.btm_outer),
            self.gap.user_setpoint.set(value=id_motor_values.gap),
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


class Apple2(abc.ABC, StandardReadable, Movable):
    """
    Apple2 Undulator Device

    The `Apple2` class represents an Apple 2 insertion device (undulator) used in synchrotron beamlines.
    This device provides additional degrees of freedom compared to standard undulators, allowing independent
    movement of magnet banks to produce X-rays with various polarisations and energies.

    The class is designed to manage the undulator's gap, phase motors, and polarisation settings, while
    abstracting hardware interactions and providing a high-level interface for beamline operations.

    The class is abstract and requires beamline-specific implementations for _set motor
     positions based on energy and polarisation.

    Attributes
    ----------
    apple2_motors : Apple2Motors
        A collection of gap and phase motor devices.
    energy : SignalR
        A soft signal for the current energy readback.
    polarisation_setpoint : SignalR
        A soft signal for the polarisation setpoint.
    polarisation : SignalRW
        A hardware-backed signal for polarisation readback and control.
    lookup_tables : dict
        A dictionary storing lookup tables for gap and phase motor positions, used for energy and polarisation conversion.
    energy_to_motor : EnergyMotorConvertor
        A callable that converts energy and polarisation to motor positions.

    Abstract Methods
    ----------------
    _set(value: float) -> None
        Abstract method to set motor positions for a given energy and polarisation.

    Methods
    -------
    determine_phase_from_hardware(...) -> tuple[Pol, float]
        Determines the polarisation and phase value based on motor positions.

    Notes
    -----
    - This class requires beamline-specific implementations of the abstract methods.
    - The device supports multiple polarisation modes, including linear horizontal (LH), linear vertical (LV),
      positive circular (PC), negative circular (NC), and linear arbitrary (LA).

    For more detail see
    `UML </_images/apple2_design.png>`__ for detail.

    .. figure:: /explanations/umls/apple2_design.png

    """

    def __init__(
        self,
        apple2_motors: Apple2Motors,
        energy_motor_convertor: EnergyMotorConvertor,
        name: str = "",
    ) -> None:
        """

        Parameters
        ----------
        id_gap: An UndulatorGap device.
        id_phase: An UndulatorPhaseAxes device.
        energy_motor_convertor: A callable that converts energy and polarisation to motor positions.
        name: Name of the device.
        """

        self.motors = apple2_motors
        self.energy_to_motor = energy_motor_convertor
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            # Store the set energy for readback.
            self.energy, self._set_energy_rbv = soft_signal_r_and_setter(
                float, initial_value=None
            )

        # Store the polarisation for setpoint. And provide readback for LH3.
        # LH3 is a special case as it is indistinguishable from LH in the hardware.
        self.polarisation_setpoint, self._polarisation_setpoint_set = (
            soft_signal_r_and_setter(Pol)
        )

        # Hardware backed read/write for polarisation.
        self.polarisation = derived_signal_rw(
            raw_to_derived=self._read_pol,
            set_derived=self._set_pol,
            pol=self.polarisation_setpoint,
            top_outer=self.motors.phase.top_outer.user_readback,
            top_inner=self.motors.phase.top_inner.user_readback,
            btm_inner=self.motors.phase.btm_inner.user_readback,
            btm_outer=self.motors.phase.btm_outer.user_readback,
            gap=self.motors.gap.user_readback,
        )
        super().__init__(name)

    def _set_pol_setpoint(self, pol: Pol) -> None:
        """Set the polarisation setpoint without moving hardware. The polarisation
        setpoint is used to determine the gap and phase motor positions when
        setting the energy/polarisation of the undulator."""
        self._polarisation_setpoint_set(pol)

    async def _set_pol(
        self,
        value: Pol,
    ) -> None:
        # This changes the pol setpoint and then changes polarisation via set energy.
        self._set_pol_setpoint(value)
        await self.set(await self.energy.get_value())

    @AsyncStatus.wrap
    async def set(self, value: float) -> None:
        """
        Set should be in energy units, this will set the energy of the ID by setting the
        gap and phase motors to the correct position for the given energy
        and polarisation.


        Examples
        --------
        RE( id.set(888.0)) # This will set the ID to 888 eV
        RE(scan([detector], id,600,700,100)) # This will scan the ID from 600 to 700 eV in 100 steps.
        """
        await self._set(value)
        self._set_energy_rbv(value)  # Update energy after move for readback.
        LOGGER.info(f"Energy set to {value} eV successfully.")

    @abc.abstractmethod
    async def _set(self, value: float) -> None:
        """
        This method should be implemented by the beamline specific ID class as the
        motor positions will be different for each beamline depending on the
        undulator design and the lookup table used. The set method can be
        used to set the motor positions for the given energy and polarisation
        provided that all motors can be moved at the same time.
        """

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
