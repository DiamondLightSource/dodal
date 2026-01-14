from typing import Generic

from numpy import sign

from dodal.common import Rectangle2D
from dodal.devices.insertion_device import (
    Apple2,
    Apple2Controller,
    Apple2Val,
    EnergyMotorConvertor,
)
from dodal.devices.insertion_device.apple2_undulator import (
    Apple2LockedPhasesVal,
    PhaseAxesType,
)
from dodal.devices.insertion_device.enum import Pol
from dodal.log import LOGGER

APPLE_KNOT_MAXIMUM_GAP_MOTOR_POSITION = 100.0
APPLE_KNOT_MAXIMUM_PHASE_MOTOR_POSITION = 70.0


class AppleKnotPathFinder:
    """
    Class to find a safe path for AppleKnot undulator moves that avoids the exclusion zone
    around 0-0 gap-phase. We rely on axis-aligned (manhattan) moves and splitting moves
    that cross zero phase into two segments via an intermediate point at zero phase and
    a safe gap value. We ASSUME the exclusion zones are rectangles aligned with the axes
    in a shape of hanoi tower centered at (0,0).
    See https://confluence.diamond.ac.uk/x/vQENAg for more details.
    """

    def __init__(
        self,
        exclusion_zone: tuple[Rectangle2D, ...],
    ) -> None:
        # Define the exclusion zone rectangles around (0,0)
        self.exclusion_zone = exclusion_zone

    def get_apple_knot_val_path(
        self, start_val: Apple2Val, end_val: Apple2Val
    ) -> tuple[Apple2Val, ...]:
        """
        Get a list of Apple2Val representing the path from start to end avoiding exclusion zones.
        """
        apple_knot_val_path = ()
        # Defensive checks for no movement
        if (
            start_val.gap == end_val.gap
            and start_val.phase.top_outer == end_val.phase.top_outer
        ):
            LOGGER.warning("Start point same as end point, no path calculated.")
            return apple_knot_val_path
        for zone in self.exclusion_zone:
            for value in (start_val, end_val):
                if zone.contains(value.phase.top_outer, value.gap):
                    LOGGER.warning(
                        "Start point is inside exclusion zone, no path calculated."
                    )
                    return apple_knot_val_path
        apple_knot_val_path += (start_val,)
        # Split the move if start and end are on opposite sides of zero phase
        if (
            sign(start_val.phase.top_outer) == (-1) * sign(end_val.phase.top_outer)
            and sign(start_val.phase.top_outer) != 0
        ):
            apple_knot_val_path += (
                self._get_zero_phase_crossing_point(start_val, end_val),
            )
        apple_knot_val_path += (end_val,)
        return self._apple_knot_manhattan_path(apple_knot_val_path)

    def _apple_knot_manhattan_path(
        self, apple_knot_val_path: tuple[Apple2Val, ...]
    ) -> tuple[Apple2Val, ...]:
        """
        Convert a list of Apple2Val into a manhattan path avoiding exclusion zones.
        Here all moves are done in axis-aligned steps (gap first then phase or vice versa).
        List of points is expanded to include intermediate points as needed so each move
        happens within one sign of gap and phase (including zero phase).
        For convenience we define:phase increase as West-East axis and gap increase
        as North-South axis. Only SW move in negative phase region and SE move in
        positive phase region need a PHASE first then GAP move, the rest needs GAP
        first then PHASE move.
        """
        final_path = []
        for i in range(len(apple_knot_val_path) - 1):
            start_val = apple_knot_val_path[i]
            end_val = apple_knot_val_path[i + 1]
            final_path.append(start_val)
            # Direct move along one axis, no intermediate point needed
            if (
                end_val.phase.top_outer == start_val.phase.top_outer
                or end_val.gap == start_val.gap
            ):
                continue
            # Determine move order based on quadrant rules
            if end_val.gap <= start_val.gap and abs(end_val.phase.top_outer) > abs(
                start_val.phase.top_outer
            ):
                # Move PHASE first then GAP (SW move in negative phase or SE move in positive phase)
                intermediate_val = Apple2Val(gap=start_val.gap, phase=end_val.phase)
                final_path.append(intermediate_val)

            else:
                # Move GAP first then PHASE (other moves)
                intermediate_val = Apple2Val(gap=end_val.gap, phase=start_val.phase)
                final_path.append(intermediate_val)
        final_path.append(apple_knot_val_path[-1])
        return tuple(final_path)

    def _get_zero_phase_crossing_point(
        self, start_val: Apple2Val, end_val: Apple2Val
    ) -> Apple2Val:
        # Calculate the point where phase crosses zero
        max_exclusion_gap = (
            max([zone.get_max_y() for zone in self.exclusion_zone])
            if self.exclusion_zone
            else 0.0
        )
        return Apple2Val(
            gap=max(
                (start_val.gap + end_val.gap) / 2, max_exclusion_gap
            ),  # Ensure gap is above a minimum value
            phase=Apple2LockedPhasesVal(
                top_outer=0.0,
                btm_inner=0.0,
            ),
        )


class AppleKnotController(Apple2Controller[Apple2], Generic[PhaseAxesType]):
    """
    Controller for Apple Knot undulator with unique feature of calculating a move path
    through gap and phase space avoiding the exclusion zone around 0-0 gap-phase.
    See https://confluence.diamond.ac.uk/x/vQENAg for more details.
    """

    def __init__(
        self,
        apple: Apple2[PhaseAxesType],
        gap_energy_motor_converter: EnergyMotorConvertor,
        phase_energy_motor_converter: EnergyMotorConvertor,
        path_finder: AppleKnotPathFinder,
        maximum_gap_motor_position: float = APPLE_KNOT_MAXIMUM_GAP_MOTOR_POSITION,
        maximum_phase_motor_position: float = APPLE_KNOT_MAXIMUM_PHASE_MOTOR_POSITION,
        units: str = "eV",
        name: str = "",
    ) -> None:
        self.path_finder = path_finder
        super().__init__(
            apple2=apple,
            gap_energy_motor_converter=gap_energy_motor_converter,
            phase_energy_motor_converter=phase_energy_motor_converter,
            maximum_gap_motor_position=maximum_gap_motor_position,
            maximum_phase_motor_position=maximum_phase_motor_position,
            units=units,
            name=name,
        )

    async def _set_energy(self, energy: float) -> None:
        pol = await self._check_and_get_pol_setpoint()
        await self._combined_move(energy, pol)
        self._energy_set(energy)

    async def _combined_move(self, energy: float, pol: Pol) -> None:
        # get current apple2 val
        gap = float(await self.apple2().gap().user_readback.get_value())
        phase = float(await self.apple2().phase().top_outer.user_readback.get_value())
        pol = await self._check_and_get_pol_setpoint()
        current_apple2_val = self._get_apple2_value(gap, phase, pol)
        # get target phase and gap
        gap = self.gap_energy_motor_converter(energy=energy, pol=pol)
        phase = self.phase_energy_motor_converter(energy=energy, pol=pol)
        target_apple2_val = self._get_apple2_value(gap, phase, pol)
        # get path avoiding exclusion zone
        manhattan_path = self.path_finder.get_apple_knot_val_path(
            current_apple2_val, target_apple2_val
        )
        if manhattan_path == ():
            raise RuntimeError("No valid path found for move avoiding exclusion zones.")
        # execute the moves along the path
        for apple2_val in manhattan_path:
            LOGGER.info(f"Moving to apple2 values: {apple2_val}")
            await self.apple2().set(id_motor_values=apple2_val)

    def _get_apple2_value(self, gap: float, phase: float, pol: Pol) -> Apple2Val:
        apple2_val = Apple2Val(
            gap=gap,
            phase=Apple2LockedPhasesVal(
                top_outer=phase,
                btm_inner=phase,
            ),
        )
        LOGGER.info(f"Getting apple2 value for pol={pol}, gap={gap}, phase={phase}.")
        LOGGER.info(f"Apple2 motor values: {apple2_val}.")
        return apple2_val
