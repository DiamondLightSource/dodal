import abc
import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np
from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    ConfigSignal,
    HintedSignal,
    StandardReadable,
    soft_signal_r_and_setter,
    wait_for_value,
)
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw, epics_signal_w
from pydantic import BaseModel

from dodal.log import LOGGER


class UndulatorGateStatus(str, Enum):
    open = "Open"
    close = "Closed"


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


class UndulatorGap(StandardReadable, Movable):
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
        # Gate keeper open when move is requested, closed when move is completed
        self.gate = epics_signal_r(UndulatorGateStatus, prefix + "BLGATE")
        # These are gap velocity limit.
        self.max_velocity = epics_signal_r(float, prefix + "BLGSETVEL.HOPR")
        self.min_velocity = epics_signal_r(float, prefix + "BLGSETVEL.LOPR")
        # These are gap limit.
        self.high_limit_travel = epics_signal_r(float, prefix + "BLGAPMTR.HLM")
        self.low_limit_travel = epics_signal_r(float, prefix + "BLGAPMTR.LLM")
        split_pv = prefix.split("-")
        self.fault = epics_signal_r(
            float,
            split_pv[0] + "-" + split_pv[1] + "-STAT" + "-" + split_pv[3] + "ANYFAULT",
        )
        # This is calculated acceleration from speed
        self.acceleration_time = epics_signal_r(float, prefix + "IDGSETACC")
        with self.add_children_as_readables(ConfigSignal):
            # Unit
            self.motor_egu = epics_signal_r(str, prefix + "BLGAPMTR.EGU")
            # Gap velocity
            self.velocity = epics_signal_rw(float, prefix + "BLGSETVEL")
        with self.add_children_as_readables(HintedSignal):
            # Gap readback value
            self.user_readback = epics_signal_r(float, prefix + "CURRGAPD")
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value) -> None:
        LOGGER.info(f"Setting {self.name} to {value}")
        await self.check_id_status()
        await self.user_setpoint.set(value=str(value))
        timeout = await self._cal_timeout()
        LOGGER.info(f"Moving {self.name} to {value} with timeout = {timeout}")
        await self.set_move.set(value=1)
        await wait_for_value(self.gate, UndulatorGateStatus.close, timeout=timeout)

    async def _cal_timeout(self) -> float:
        vel = await self.velocity.get_value()
        cur_pos = await self.user_readback.get_value()
        target_pos = float(await self.user_setpoint.get_value())
        return abs((target_pos - cur_pos) * 2.0 / vel)

    async def check_id_status(self) -> None:
        if await self.fault.get_value() != 0:
            raise RuntimeError(f"{self.name} is in fault state")
        if await self.gate.get_value() == UndulatorGateStatus.open:
            raise RuntimeError(f"{self.name} is already in motion.")

    async def get_timeout(self) -> float:
        return await self._cal_timeout()


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
        self.user_setpoint = epics_signal_w(str, "SET")
        self.user_setpoint_demand_readback = epics_signal_r(float, "DMD")

        fullPV = fullPV + "MTR"
        with self.add_children_as_readables(HintedSignal):
            self.user_setpoint_readback = epics_signal_r(float, fullPV + ".RBV")

        with self.add_children_as_readables(ConfigSignal):
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


class UndlatorPhaseAxes(StandardReadable, Movable):
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
        # Nothing move until this is set to 1 and it will return to 0 when done
        self.set_move = epics_signal_rw(int, prefix + "BLGSETP")
        self.gate = epics_signal_r(UndulatorGateStatus, prefix + "BLGATE")
        split_pv = prefix.split("-")
        temp_pv = f"{split_pv[0]}-{split_pv[1]}-STAT-{split_pv[3]}ANYFAULT"
        self.fault = epics_signal_r(float, temp_pv)
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, value: Apple2PhasesVal) -> None:
        LOGGER.info(f"Setting {self.name} to {value}")

        await self.check_id_status()

        await asyncio.gather(
            self.top_outer.user_setpoint.set(value=value.top_outer),
            self.top_inner.user_setpoint.set(value=value.top_inner),
            self.btm_inner.user_setpoint.set(value=value.btm_inner),
            self.btm_outer.user_setpoint.set(value=value.btm_outer),
        )
        timeout = await self._cal_timeout()
        await self.set_move.set(value=1)
        await wait_for_value(self.gate, UndulatorGateStatus.close, timeout=timeout)

    async def _cal_timeout(self) -> float:
        """
        Get all four motor speed, current positions and target positions to calculate required timeout.
        """
        velos = await asyncio.gather(
            self.top_outer.velocity.get_value(),
            self.top_inner.velocity.get_value(),
            self.btm_inner.velocity.get_value(),
            self.btm_outer.velocity.get_value(),
        )
        target_pos = await asyncio.gather(
            self.top_outer.user_setpoint_demand_readback.get_value(),
            self.top_inner.user_setpoint_demand_readback.get_value(),
            self.btm_inner.user_setpoint_demand_readback.get_value(),
            self.btm_outer.user_setpoint_demand_readback.get_value(),
        )
        cur_pos = await asyncio.gather(
            self.top_outer.user_setpoint_readback.get_value(),
            self.top_inner.user_setpoint_readback.get_value(),
            self.btm_inner.user_setpoint_readback.get_value(),
            self.btm_outer.user_setpoint_readback.get_value(),
        )
        move_distances = tuple(np.subtract(target_pos, cur_pos))
        move_times = np.abs(np.divide(move_distances, velos))
        longest_move_time = np.max(move_times)
        return longest_move_time * 2

    async def check_id_status(self) -> None:
        if await self.fault.get_value() != 0:
            raise RuntimeError(f"{self.name} is in fault state")
        if await self.gate.get_value() == UndulatorGateStatus.open:
            raise RuntimeError(f"{self.name} is already in motion.")

    async def get_timeout(self) -> float:
        return await self._cal_timeout()


class EnergyMinMax(BaseModel):
    Minimum: float
    Maximum: float


class EnergyCoverageEntry(BaseModel):
    Low: float
    High: float
    Poly: np.poly1d

    class Config:
        arbitrary_types_allowed = True


class EnergyCoverage(BaseModel):
    __root__: dict[str, EnergyCoverageEntry]


class LookupTableEntries(BaseModel):
    Energies: EnergyCoverage
    Limit: EnergyMinMax


class Lookuptable(BaseModel):
    """
    BaseModel class for the lookup table.
    Appl2 lookup table should be in this format.

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

    __root__: dict[str, LookupTableEntries]


ROW_PHASE_MOTOR_TOLERANCE = 0.004
MAXIMUM_ROW_PHASE_MOTOR_POSITION = 24.0
MAXIMUM_GAP_MOTOR_POSITION = 100


class Apple2(StandardReadable, Movable):
    """
    Apple 2 ID/undulator has 4 extra degrees of freedom compare to the standard Undulator,
     each bank of magnet can move independently to each other,
     which allow the production of different x-ray polarisation as well as energy.
     This type of ID is use on I10, I21, I09, I17 and I06 for soft x-ray.

    A pair of look up tables are needed to provide the conversion between motor position and energy.

    An new definition of Set and update_lookuptable method is required.


    Parameters
    ----------
    id_gap:
        An UndulatorGap device.
    id_phase:
        An UndlatorPhaseAxes device.
    prefix:
        Not in use but needed for device_instantiation.
    name:
        Name of the device.
    """

    def __init__(
        self,
        id_gap: UndulatorGap,
        id_phase: UndlatorPhaseAxes,
        prefix: str = "",
        name: str = "",
    ) -> None:
        super().__init__(name)

        # Attributes are set after super call so they are not renamed to
        # <name>-undulator, etc.
        with self.add_children_as_readables():
            self.gap = id_gap
            self.phase = id_phase
        with self.add_children_as_readables(HintedSignal):
            # Store the polarisation for readback.
            self.polarisation, self._polarisation_set = soft_signal_r_and_setter(
                str, initial_value=None
            )
            # Store the set energy for readback.
            self.energy, self._energy_set = soft_signal_r_and_setter(
                float, initial_value=None
            )
        # This store two lookup tables, Gap and Phase in the Lookuptable format
        self.lookup_tables: dict[str, dict[str | None, dict[str, dict[str, Any]]]] = {
            "Gap": {},
            "Phase": {},
        }
        # List of available polarisation according to the lookup table.
        self._available_pol = []
        # The polarisation state of the id that are use for internal checking before setting.
        self._pol = None
        """
        Abstract method that run at start up to load lookup tables into  self.lookup_tables
         and set available_pol.
        """
        self.update_lookuptable()

    @property
    def pol(self):
        return self._pol

    @pol.setter
    def pol(self, pol: str):
        # This set the polarisation but does not actually move hardware.
        if pol in self._available_pol:
            self._pol = pol
        else:
            raise ValueError(
                f"Polarisation {pol} is not available:"
                + f"/n Polarisations available:  {self._available_pol}"
            )

    async def _set(self, value: Apple2Val, energy: float) -> None:
        """
        Check ID is in a movable state and set all the demand value before moving.

        """

        # Only need to check gap as the phase motors share both fault and gate with gap.
        await self.gap.check_id_status()
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
            f"Moving f{self.name} energy and polorisation to {energy}, {self.pol}"
            + f"with motor position {value}, timeout = {timeout}"
        )
        await self.gap.set_move.set(value=1)
        await wait_for_value(self.gap.gate, UndulatorGateStatus.close, timeout=timeout)
        self._energy_set(energy)  # Update energy for after move for readback.

    def _get_id_gap_phase(self, energy: float) -> tuple[float, float]:
        """
        Converts energy and polarisation to gap and phase.
        """
        gap_poly = self._get_poly(
            lookup_table=self.lookup_tables["Gap"], new_energy=energy
        )
        phase_poly = self._get_poly(
            lookup_table=self.lookup_tables["Phase"], new_energy=energy
        )
        return gap_poly(energy), phase_poly(energy)

    def _get_poly(
        self,
        new_energy: float,
        lookup_table: dict[str | None, dict[str, dict[str, Any]]],
    ) -> np.poly1d:
        """
        Get the correct polynomial for a given energy form lookuptable
         for any given polarisation.
        """

        if (
            new_energy < lookup_table[self.pol]["Limit"]["Minimum"]
            or new_energy > lookup_table[self.pol]["Limit"]["Maximum"]
        ):
            raise ValueError(
                "Demanding energy must lie between {} and {} eV!".format(
                    lookup_table[self.pol]["Limit"]["Minimum"],
                    lookup_table[self.pol]["Limit"]["Maximum"],
                )
            )
        else:
            for energy_range in lookup_table[self.pol]["Energies"].values():
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
            Lookuptable.parse_obj(<loockuptable>)

        """

    async def determinePhaseFromHardware(self) -> tuple[str | None, float]:
        """
        Try to determine polarisation and phase value using row phase motor position pattern.
        However there is no way to return lh3 polarisation or higher harmonic setting.
        (May be for future one can use the inverse poly to work out the energy and try to match it with the current energy
        to workout the polarisation but during my test the inverse poly is too unstable for general use.)
        """
        cur_loc = await self.read()
        top_outer = cur_loc[self.phase.top_outer.user_setpoint_readback.name]["value"]
        top_inner = cur_loc[self.phase.top_inner.user_setpoint_readback.name]["value"]
        btm_inner = cur_loc[self.phase.btm_inner.user_setpoint_readback.name]["value"]
        btm_outer = cur_loc[self.phase.btm_outer.user_setpoint_readback.name]["value"]
        gap = cur_loc[self.gap.user_readback.name]["value"]
        if gap > MAXIMUM_GAP_MOTOR_POSITION:
            raise RuntimeError(
                f"{self.name} is not in use, close gap or set polarisation to use this ID"
            )

        if all(
            motor_position_equal(x, 0.0)
            for x in [top_outer, top_inner, btm_inner, btm_outer]
        ):
            # Linear Horizontal
            polarisation = "lh"
            phase = 0.0
            return polarisation, phase
        if (
            motor_position_equal(top_outer, MAXIMUM_ROW_PHASE_MOTOR_POSITION)
            and motor_position_equal(top_inner, 0.0)
            and motor_position_equal(btm_inner, MAXIMUM_ROW_PHASE_MOTOR_POSITION)
            and motor_position_equal(btm_outer, 0.0)
        ):
            # Linear Vertical
            polarisation = "lv"
            phase = MAXIMUM_ROW_PHASE_MOTOR_POSITION
            return polarisation, phase
        if (
            motor_position_equal(top_outer, btm_inner)
            and top_outer > 0.0
            and motor_position_equal(top_inner, 0.0)
            and motor_position_equal(btm_outer, 0.0)
        ):
            # Positive Circular
            polarisation = "pc"
            phase = top_outer
            return polarisation, phase
        if (
            motor_position_equal(top_outer, btm_inner)
            and top_outer < 0.0
            and motor_position_equal(top_inner, 0.0)
            and motor_position_equal(btm_outer, 0.0)
        ):
            # Negative Circular
            polarisation = "nc"
            phase = top_outer
            return polarisation, phase
        if (
            motor_position_equal(top_outer, -btm_inner)
            and motor_position_equal(top_inner, 0.0)
            and motor_position_equal(btm_outer, 0.0)
        ):
            # Positive Linear Arbitrary
            polarisation = "la"
            phase = top_outer
            return polarisation, phase
        if (
            motor_position_equal(top_inner, -btm_outer)
            and motor_position_equal(top_outer, 0.0)
            and motor_position_equal(btm_inner, 0.0)
        ):
            # Negative Linear Arbitrary
            polarisation = "la"
            phase = top_inner
            return polarisation, phase
        # UNKNOWN default
        polarisation = None
        phase = 0.0
        return (polarisation, phase)


def motor_position_equal(a, b) -> bool:
    """
    Check motor is within tolerance.
    """
    return abs(a - b) < ROW_PHASE_MOTOR_TOLERANCE
