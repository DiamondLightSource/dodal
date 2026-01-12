import abc
from math import isclose
from typing import Generic, Protocol, TypeVar

from ophyd_async.core import (
    Reference,
    StandardReadable,
    StandardReadableFormat,
    derived_signal_rw,
    soft_signal_r_and_setter,
    soft_signal_rw,
)

from dodal.common import Rectangle2D, sign
from dodal.devices.insertion_device.apple2_undulator import (
    Apple2,
    Apple2PhasesVal,
    Apple2Val,
    UndulatorPhaseAxes,
)
from dodal.devices.insertion_device.energy_motor_lookup import (
    EnergyMotorLookup,
)
from dodal.devices.insertion_device.enum import Pol
from dodal.log import LOGGER

T = TypeVar("T")
MAXIMUM_MOVE_TIME = 550  # There is no useful movements take longer than this.
ROW_PHASE_MOTOR_TOLERANCE = 0.004
MAXIMUM_ROW_PHASE_MOTOR_POSITION = 24.0
MAXIMUM_GAP_MOTOR_POSITION = 100


class EnergyMotorConvertor(Protocol):
    def __call__(self, energy: float, pol: Pol) -> float:
        """Protocol to provide energy to motor position conversion"""
        ...


Apple2Type = TypeVar("Apple2Type", bound=Apple2)


class Apple2Controller(abc.ABC, StandardReadable, Generic[Apple2Type]):
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
    gap_energy_to_motor_converter : EnergyMotorConvertor
        Callable that converts energy and polarisation to gap motor positions.
    phase_energy_to_motor_converter : EnergyMotorConvertor
        Callable that converts energy and polarisation to phase motor positions.

    Abstract Methods
    ----------------
    _get_apple2_value(gap: float, phase: float) -> Apple2Val
        Abstract method to return the Apple2Val used to set the apple2 with.
    Notes
    -----
    - Subclasses must implement `_get_apple2_value` for beamline-specific logic.
    - LH3 polarisation is indistinguishable from LH in hardware; special handling is provided.
    - Supports multiple polarisation modes, including linear horizontal (LH), linear vertical (LV),
      positive circular (PC), negative circular (NC), and linear arbitrary (LA).

    """

    def __init__(
        self,
        apple2: Apple2Type,
        gap_energy_motor_converter: EnergyMotorConvertor,
        phase_energy_motor_converter: EnergyMotorConvertor,
        units: str = "eV",
        name: str = "",
    ) -> None:
        """

        Parameters
        ----------
        apple2: Apple2
            An Apple2 device.
        gap_energy_motor_converter: EnergyMotorConvertor
            The callable that handles the gap look up table logic for the insertion device.
        phase_energy_motor_converter: EnergyMotorConvertor
            The callable that handles the phase look up table logic for the insertion device.
        units: str
            the units of this device. Defaults to eV.
        name: str
            Name of the device.
        """
        self.apple2_ref = Reference(apple2)
        self.gap_energy_motor_converter = gap_energy_motor_converter
        self.phase_energy_motor_converter = phase_energy_motor_converter

        # Store the set energy for readback.
        self._energy, self._energy_set = soft_signal_r_and_setter(
            float, initial_value=None, units=units
        )
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.energy = derived_signal_rw(
                raw_to_derived=self._read_energy,
                set_derived=self._set_energy,
                energy=self._energy,
                derived_units=units,
            )

        # Store the polarisation for setpoint. And provide readback for LH3.
        # LH3 is a special case as it is indistinguishable from LH in the hardware.
        self.polarisation_setpoint, self._polarisation_setpoint_set = (
            soft_signal_r_and_setter(Pol)
        )
        phase = self.apple2_ref().phase_ref()
        # check if undulator phase is unlocked.
        if isinstance(phase, UndulatorPhaseAxes):
            top_inner = phase.top_inner.user_readback
            btm_outer = phase.btm_outer.user_readback
        else:
            # If locked phase axes make the locked phase 0.
            top_inner = btm_outer = soft_signal_rw(float, initial_value=0.0)

        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            # Hardware backed read/write for polarisation.

            self.polarisation = derived_signal_rw(
                raw_to_derived=self._read_pol,
                set_derived=self._set_pol,
                pol=self.polarisation_setpoint,
                top_outer=phase.top_outer.user_readback,
                top_inner=top_inner,
                btm_inner=phase.btm_inner.user_readback,
                btm_outer=btm_outer,
                gap=self.apple2_ref().gap_ref().user_readback,
            )
        super().__init__(name)

    @abc.abstractmethod
    def _get_apple2_value(self, gap: float, phase: float, pol: Pol) -> Apple2Val:
        """
        This method should be implemented by the beamline specific ID class as the
        motor positions will be different for each beamline depending on the
        undulator design.
        """

    async def _get_current_apple2_value(self) -> Apple2Val:
        gap = float(await self.apple2_ref().gap_ref().user_setpoint.get_value())
        phase = await self.apple2_ref().phase_ref().user_setpoint.get_value()
        pol = await self._check_and_get_pol_setpoint()
        return self._get_apple2_value(gap, phase, pol)

    async def _set_motors_from_energy_and_polarisation(
        self, energy: float, pol: Pol
    ) -> None:
        """Set the undulator motors for a given energy and polarisation."""
        gap = self.gap_energy_motor_converter(energy=energy, pol=pol)
        phase = self.phase_energy_motor_converter(energy=energy, pol=pol)
        apple2_val = self._get_apple2_value(gap, phase, pol)
        LOGGER.info(f"Setting polarisation to {pol}, with values: {apple2_val}")
        await self.apple2_ref().set(id_motor_values=apple2_val)

    async def _set_energy(self, energy: float) -> None:
        pol = await self._check_and_get_pol_setpoint()
        await self._set_motors_from_energy_and_polarisation(energy, pol)
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
        await self.energy.set(await self.energy.get_value(), timeout=MAXIMUM_MOVE_TIME)

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


class Apple2EnforceLHMoveController(Apple2Controller[Apple2]):
    """The latest Apple2 version allows unrestricted motor movement.
    However, because of the high forces involved in polarization changes,
    all movements must be performed using the Linear Horizontal (LH) mode.
    A look-up table must also be used to determine the highest energy that can
    be reached in LH mode."""

    def __init__(
        self,
        apple2: Apple2,
        gap_energy_motor_lut: EnergyMotorLookup,
        phase_energy_motor_lut: EnergyMotorLookup,
        units: str = "eV",
        name: str = "",
    ) -> None:
        self.gap_energy_motor_lu = gap_energy_motor_lut
        self.phase_energy_motor_lu = phase_energy_motor_lut
        super().__init__(
            apple2=apple2,
            gap_energy_motor_converter=gap_energy_motor_lut.find_value_in_lookup_table,
            phase_energy_motor_converter=phase_energy_motor_lut.find_value_in_lookup_table,
            units=units,
            name=name,
        )

    def _get_apple2_value(self, gap: float, phase: float, pol: Pol) -> Apple2Val:
        apple2_val = Apple2Val(
            gap=gap,
            phase=Apple2PhasesVal(
                top_outer=phase,
                top_inner=0.0,
                btm_inner=phase,
                btm_outer=0.0,
            ),
        )
        LOGGER.info(f"Getting apple2 value for pol={pol}, gap={gap}, phase={phase}.")
        LOGGER.info(f"Apple2 motor values: {apple2_val}.")

        return apple2_val

    async def _set_pol(
        self,
        value: Pol,
    ) -> None:
        # I09/I21 require all polarisation change to go via LH.
        current_pol = await self.polarisation.get_value()
        if current_pol == value:
            LOGGER.info(f"Polarisation already at {value}")
        else:
            target_energy = await self.energy.get_value()
            if (value is not Pol.LH) and (current_pol is not Pol.LH):
                self._polarisation_setpoint_set(Pol.LH)
                max_lh_energy = float(
                    self.gap_energy_motor_lu.lut.root[Pol("lh")].max_energy
                )
                lh_setpoint = (
                    max_lh_energy if target_energy > max_lh_energy else target_energy
                )
                LOGGER.info(f"Changing polarisation to {value} via {Pol.LH}")
                await self.energy.set(lh_setpoint, timeout=MAXIMUM_MOVE_TIME)
            self._polarisation_setpoint_set(value)
            await self.energy.set(target_energy, timeout=MAXIMUM_MOVE_TIME)


class AppleKnotController(Apple2Controller[Apple2]):
    """
    Controller for Apple Knot undulator with unique feature of calculating a move path
    through gap and phase space which avoids the exclusion zone around 0-0 gap-phase.
    See https://confluence.diamond.ac.uk/x/vQENAg for more details.
    """

    def __init__(
        self,
        apple: Apple2,
        gap_energy_motor_converter: EnergyMotorConvertor,
        phase_energy_motor_converter: EnergyMotorConvertor,
        exclusion_zone: list[Rectangle2D],
        units: str = "eV",
        name: str = "",
    ) -> None:
        self.path_finder = AppleKnotPathFinder(exclusion_zone=exclusion_zone)
        super().__init__(
            apple2=apple,
            gap_energy_motor_converter=gap_energy_motor_converter,
            phase_energy_motor_converter=phase_energy_motor_converter,
            units=units,
            name=name,
        )

    async def _set_energy(self, energy: float) -> None:
        pol = await self._check_and_get_pol_setpoint()
        await self._combined_move(energy, pol)
        self._energy_set(energy)

    async def _combined_move(self, energy: float, pol: Pol) -> None:
        # get current apple2 val
        current_apple2_val = await self._get_current_apple2_value()
        # get target phase and gap
        gap = self.gap_energy_motor_converter(energy=energy, pol=pol)
        phase = self.phase_energy_motor_converter(energy=energy, pol=pol)
        target_apple2_val = self._get_apple2_value(gap, phase, pol)
        # get path avoiding exclusion zone
        for apple2_val in self.path_finder.get_apple_knot_val_path(
            current_apple2_val, target_apple2_val
        ):
            LOGGER.info(f"Moving to apple2 values: {apple2_val}")
            await self.apple2_ref().set(id_motor_values=apple2_val)

    def _get_apple2_value(self, gap: float, phase: float, pol: Pol) -> Apple2Val:
        apple2_val = Apple2Val(
            gap=gap,
            phase=Apple2PhasesVal(
                top_outer=phase,
                top_inner=0.0,
                btm_inner=phase,
                btm_outer=0.0,
            ),
        )
        LOGGER.info(f"Getting apple2 value for pol={pol}, gap={gap}, phase={phase}.")
        LOGGER.info(f"Apple2 motor values: {apple2_val}.")

        return apple2_val


class AppleKnotPathFinder:
    """
    Class to find a safe path for AppleKnot undulator moves that avoids the exclusion zone
    around 0-0 gap-phase. See https://confluence.diamond.ac.uk/x/vQENAg for more details.
    """

    def __init__(
        self,
        exclusion_zone: list[Rectangle2D],
    ) -> None:
        # Define the exclusion zone rectangles around (0,0)
        self.exclusion_zone = exclusion_zone if exclusion_zone is not None else []

    def get_apple_knot_val_path(
        self, start_val: Apple2Val, end_val: Apple2Val
    ) -> list[Apple2Val]:
        """
        Get a list of Apple2Val representing the path from start to end avoiding exclusion zones.
        """
        apple_knot_val_path = []
        # Defensive checks for no movement
        if (
            start_val.gap == end_val.gap
            and start_val.phase.top_outer == end_val.phase.top_outer
        ):
            LOGGER.warning("Start point same as end point, no path calculated.")
            return apple_knot_val_path
        if [
            zone.contains(start_val.gap, start_val.phase.top_outer)
            or zone.contains(end_val.gap, end_val.phase.top_outer)
            for zone in self.exclusion_zone
        ]:
            LOGGER.warning("Start point is inside exclusion zone, no path calculated.")
            return apple_knot_val_path
        apple_knot_val_path.append(start_val)
        # Split the move if it pass phase 0 line
        if sign(start_val.phase.top_outer) == (-1) * sign(end_val.phase.top_outer):
            apple_knot_val_path.append(
                self.get_zero_phase_crossing_point(start_val, end_val)
            )
        apple_knot_val_path.append(end_val)
        return self.apple_knot_manhattan_path(apple_knot_val_path)

    def apple_knot_manhattan_path(
        self, apple_knot_val_path: list[Apple2Val]
    ) -> list[Apple2Val]:
        """
        Convert a list of Apple2Val into a manhattan path avoiding exclusion zones.
        Here all moves are done in axis-aligned steps (gap first then phase or vice versa).
        List of points is expanded to include intermediate points as needed so each move
        happens within one sign of gap and phase (including zero phase).
        """
        final_path = []
        for i in range(len(apple_knot_val_path) - 1):
            start_val = apple_knot_val_path[i]
            end_val = apple_knot_val_path[i + 1]
            final_path.append(start_val)
            if end_val.gap <= start_val.gap and abs(end_val.phase.top_outer) > abs(
                start_val.phase.top_outer
            ):
                # Move phase first then gap
                intermediate_val = Apple2Val(gap=start_val.gap, phase=end_val.phase)
                final_path.append(intermediate_val)

            else:  # Move gap first then phase
                intermediate_val = Apple2Val(gap=end_val.gap, phase=start_val.phase)
                final_path.append(intermediate_val)
        final_path.append(apple_knot_val_path[-1])
        return final_path

    def get_zero_phase_crossing_point(
        self, start_val: Apple2Val, end_val: Apple2Val
    ) -> Apple2Val:
        # Calculate the point where phase crosses zero
        # This is a simplified version - in practice, you'd use a more complex algorithm
        # to find the exact crossing point in the exclusion zone
        max_exclusion_gap = (
            max([zone.get_max_y() for zone in self.exclusion_zone])
            if self.exclusion_zone
            else 0.0
        )

        return Apple2Val(
            gap=max(
                (start_val.gap + end_val.gap) / 2, max_exclusion_gap
            ),  # Ensure gap is above a minimum value
            phase=Apple2PhasesVal(
                top_outer=0.0,
                top_inner=0.0,
                btm_inner=0.0,
                btm_outer=0.0,
            ),
        )
