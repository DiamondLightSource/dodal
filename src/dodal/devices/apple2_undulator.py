import abc
import asyncio
from dataclasses import dataclass
from math import isclose
from typing import Any, Generic, TypeVar

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
from pydantic import BaseModel, ConfigDict, RootModel

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


class EnergyMinMax(BaseModel):
    Minimum: float
    Maximum: float


class EnergyCoverageEntry(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    Low: float
    High: float
    Poly: np.poly1d


class EnergyCoverage(RootModel):
    root: dict[str, EnergyCoverageEntry]


class LookupTableEntries(BaseModel):
    Energies: EnergyCoverage
    Limit: EnergyMinMax


class Lookuptable(RootModel):
    """BaseModel class for the lookup table.
    Apple2 lookup table should be in this format.

    {mode: {'Energies': {Any: {'Low': float,
                            'High': float,
                            'Poly':np.poly1d
                            }
                        }
            'Limit': {'Minimum': float,
                    'Maximum': float
                    }
        }
    }
    """

    root: dict[str, LookupTableEntries]


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


class Apple2(abc.ABC, StandardReadable, Movable):
    """
    Apple2 Undulator Device

    The `Apple2` class represents an Apple 2 insertion device (undulator) used in synchrotron beamlines.
    This device provides additional degrees of freedom compared to standard undulators, allowing independent
    movement of magnet banks to produce X-rays with various polarisations and energies.

    The class is designed to manage the undulator's gap, phase motors, and polarisation settings, while
    abstracting hardware interactions and providing a high-level interface for beamline operations.


    A pair of look up tables are needed to provide the conversion between motor position
    and energy.

    Attributes
    ----------
    gap : UndulatorGap
        The gap control device for the undulator.
    phase : UndulatorPhaseAxes
        The phase control device, consisting of four phase motors.
    energy : SignalR
        A soft signal for the current energy readback.
    polarisation_setpoint : SignalR
        A soft signal for the polarisation setpoint.
    polarisation : SignalRW
        A hardware-backed signal for polarisation readback and control.
    lookup_tables : dict
        A dictionary storing lookup tables for gap and phase motor positions, used for energy and polarisation conversion.
    _available_pol : list
        A list of available polarisations supported by the device.

    Abstract Methods
    ----------------
    set(value: float) -> None
        Abstract method to set motor positions for a given energy and polarisation.
    update_lookuptable() -> None
        Abstract method to load and validate lookup tables from external sources.

    Methods
    -------
    _set_pol_setpoint(pol: Pol) -> None
        Sets the polarisation setpoint without moving hardware.
    determine_phase_from_hardware(...) -> tuple[Pol, float]
        Determines the polarisation and phase value based on motor positions.

    Notes
    -----
    - This class requires beamline-specific implementations of the abstract methods.
    - The lookup tables must follow the `Lookuptable` format and be validated before use.
    - The device supports multiple polarisation modes, including linear horizontal (LH), linear vertical (LV),
      positive circular (PC), negative circular (NC), and linear arbitrary (LA).

    For more detail see
    `UML </_images/apple2_design.png>`__ for detail.

    .. figure:: /explanations/umls/apple2_design.png

    """

    def __init__(
        self,
        id_gap: UndulatorGap,
        id_phase: UndulatorPhaseAxes,
        prefix: str = "",
        name: str = "",
    ) -> None:
        """

        Parameters
        ----------
        id_gap: An UndulatorGap device.
        id_phase: An UndulatorPhaseAxes device.
        prefix: Not in use but needed for device_instantiation.
        name: Name of the device.
        """
        super().__init__(name)

        # Attributes are set after super call so they are not renamed to
        # <name>-undulator, etc.
        self.gap = id_gap
        self.phase = id_phase

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
        # This store two lookup tables, Gap and Phase in the Lookuptable format
        self.lookup_tables: dict[str, dict[str | None, dict[str, dict[str, Any]]]] = {
            "Gap": {},
            "Phase": {},
        }
        # Hardware backed read/write for polarisation.
        self.polarisation = derived_signal_rw(
            raw_to_derived=self._read_pol,
            set_derived=self._set_pol,
            pol=self.polarisation_setpoint,
            top_outer=self.phase.top_outer.user_readback,
            top_inner=self.phase.top_inner.user_readback,
            btm_inner=self.phase.btm_inner.user_readback,
            btm_outer=self.phase.btm_outer.user_readback,
            gap=id_gap.user_readback,
        )

        self._available_pol = []
        """
        Abstract method that run at start up to load lookup tables into  self.lookup_tables
        and set available_pol.
        """
        self.update_lookuptable()

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

    @abc.abstractmethod
    @AsyncStatus.wrap
    async def set(self, value: float) -> None:
        """
        Set should be in energy units, this will set the energy of the ID by setting the
        gap and phase motors to the correct position for the given energy
        and polarisation.
        This method should be implemented by the beamline specific ID class as the
        motor positions will be different for each beamline depending on the
        undulator design and the lookup table used.
        _set can be used to set the motor positions for the given energy and
        polarisation provided that all motors can be moved at the same time.

        Examples
        --------
        >>> RE( id.set(888.0)) # This will set the ID to 888 eV
        >>> RE(scan([detector], id,600,700,100)) # This will scan the ID from 600 to 700 eV in 100 steps.
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

    async def _set(self, value: Apple2Val, energy: float) -> None:
        """
        Check ID is in a movable state and set all the demand value before moving them
        all at the same time. This should be modified by the beamline specific ID class
        , if the ID motors has to move in a specific order.
        """

        # Only need to check gap as the phase motors share both fault and gate with gap.
        await self.gap.raise_if_cannot_move()
        await asyncio.gather(
            self.phase.top_outer.user_setpoint.set(value=value.top_outer),
            self.phase.top_inner.user_setpoint.set(value=value.top_inner),
            self.phase.btm_inner.user_setpoint.set(value=value.btm_inner),
            self.phase.btm_outer.user_setpoint.set(value=value.btm_outer),
            self.gap.user_setpoint.set(value=value.gap),
        )
        timeout = np.max(
            await asyncio.gather(self.gap.get_timeout(), self.phase.get_timeout())
        )
        LOGGER.info(
            f"Moving f{self.name} energy and polorisation to {energy}, {await self.polarisation.get_value()}"
            + f"with motor position {value}, timeout = {timeout}"
        )
        await asyncio.gather(
            self.gap.set_move.set(value=1, wait=False, timeout=timeout),
            self.phase.set_move.set(value=1, wait=False, timeout=timeout),
        )
        await wait_for_value(self.gap.gate, UndulatorGateStatus.CLOSE, timeout=timeout)
        self._set_energy_rbv(energy)  # Update energy after move for readback.

    async def _get_id_gap_phase(self, energy: float) -> tuple[float, float]:
        """
        Converts energy and polarisation to gap and phase.
        """
        gap_poly = await self._get_poly(
            lookup_table=self.lookup_tables["Gap"], new_energy=energy
        )
        phase_poly = await self._get_poly(
            lookup_table=self.lookup_tables["Phase"], new_energy=energy
        )
        return gap_poly(energy), phase_poly(energy)

    async def _get_poly(
        self,
        new_energy: float,
        lookup_table: dict[str | None, dict[str, dict[str, Any]]],
    ) -> np.poly1d:
        """
        Get the correct polynomial for a given energy form lookuptable
        for the current polarisation setpoint.
        Parameters
        ----------
        new_energy : float
            The energy in eV for which the polynomial is requested.
        lookup_table : dict[str | None, dict[str, dict[str, Any]]]
            The lookup table containing polynomial coefficients for different energies
            and polarisations.
        Returns
        -------
        np.poly1d
            The polynomial coefficients for the requested energy and polarisation.
        Raises
        ------
        ValueError
            If the requested energy is outside the limits defined in the lookup table
            or if no polynomial coefficients are found for the requested energy.
        """
        pol = await self.polarisation_setpoint.get_value()
        if (
            new_energy < lookup_table[pol]["Limit"]["Minimum"]
            or new_energy > lookup_table[pol]["Limit"]["Maximum"]
        ):
            raise ValueError(
                "Demanding energy must lie between {} and {} eV!".format(
                    lookup_table[pol]["Limit"]["Minimum"],
                    lookup_table[pol]["Limit"]["Maximum"],
                )
            )
        else:
            for energy_range in lookup_table[pol]["Energies"].values():
                if (
                    new_energy >= energy_range["Low"]
                    and new_energy < energy_range["High"]
                ):
                    return energy_range["Poly"]

        raise ValueError(
            """Cannot find polynomial coefficients for your requested energy.
        There might be gap in the calibration lookup table."""
        )

    @abc.abstractmethod
    def update_lookuptable(self) -> None:
        """
        Abstract method to update the stored lookup tabled from file.
        This function should include check to ensure the lookuptable is in the correct format:
            # ensure the importing lookup table is the correct format
            Lookuptable.model_validate(<loockuptable>)

        """

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
