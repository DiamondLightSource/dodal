import asyncio
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

import numpy as np
from bluesky.plan_stubs import mv
from bluesky.protocols import Flyable
from numpy import ndarray
from ophyd_async.core import (
    AsyncStatus,
    Device,
    Signal,
    SignalRW,
    StandardReadable,
    derived_signal_r,
    wait_for_value,
)
from ophyd_async.epics.core import (
    epics_signal_r,
    epics_signal_rw,
    epics_signal_rw_rbv,
    epics_signal_x,
)
from pydantic import field_validator
from pydantic.dataclasses import dataclass

from dodal.log import LOGGER
from dodal.parameters.experiment_parameter_base import AbstractExperimentWithBeamParams


@dataclass
class GridAxis:
    start: float
    step_size_mm: float
    full_steps: int

    def steps_to_motor_position(self, steps):
        """Gives the motor position based on steps, where steps are 0 indexed"""
        return self.start + self.step_size_mm * steps

    @property
    def end(self):
        """Gives the point where the final frame is taken"""
        # Note that full_steps is one indexed e.g. if there is one step then the end is
        # refering to the first position
        return self.steps_to_motor_position(self.full_steps - 1)

    def is_within(self, steps: float):
        """
        Determine whether a single axis coordinate is within the grid.
        The coordinate is from a continuous coordinate space based on the
        XRC grid where the origin corresponds to the centre of the first grid box.

        Args:
            steps: The coordinate to check

        Returns:
            True if the coordinate falls within the grid.
        """
        return -0.5 <= steps <= self.full_steps - 0.5


class GridScanParamsCommon(AbstractExperimentWithBeamParams):
    """
    Common holder class for the parameters of a grid scan in a similar
    layout to EPICS. The parameters and functions of this class are common
    to both the zebra and panda triggered fast grid scans.

    The grid specified is where data is taken e.g. it can be assumed the first frame is
    at x_start, y1_start, z1_start and subsequent frames are N*step_size away.
    """

    x_steps: int = 1
    y_steps: int = 1
    z_steps: int = 0
    x_step_size_mm: float = 0.1
    y_step_size_mm: float = 0.1
    z_step_size_mm: float = 0.1
    x_start_mm: float = 0.1
    y1_start_mm: float = 0.1
    y2_start_mm: float = 0.1
    z1_start_mm: float = 0.1
    z2_start_mm: float = 0.1

    # Whether to set the stub offsets after centering
    set_stub_offsets: bool = False

    @property
    def x_axis(self) -> GridAxis:
        return GridAxis(self.x_start_mm, self.x_step_size_mm, self.x_steps)

    @property
    def y_axis(self) -> GridAxis:
        return GridAxis(self.y1_start_mm, self.y_step_size_mm, self.y_steps)

    @property
    def z_axis(self) -> GridAxis:
        return GridAxis(self.z2_start_mm, self.z_step_size_mm, self.z_steps)

    def get_num_images(self):
        return self.x_steps * (self.y_steps + self.z_steps)

    @property
    def is_3d_grid_scan(self):
        return self.z_steps > 0

    def grid_position_to_motor_position(self, grid_position: ndarray) -> ndarray:
        """Converts a grid position, given as steps in the x, y, z grid,
        to a real motor position.

        Args:
            grid_position: The x, y, z position in grid steps. The origin is at the
                centre of the first grid box
        Returns:
            The motor position this corresponds to.
        Raises:
            IndexError if the desired position is outside the grid.
        """
        for position, axis in zip(
            grid_position, [self.x_axis, self.y_axis, self.z_axis], strict=False
        ):
            if not axis.is_within(position):
                raise IndexError(f"{grid_position} is outside the bounds of the grid")

        return np.array(
            [
                self.x_axis.steps_to_motor_position(grid_position[0]),
                self.y_axis.steps_to_motor_position(grid_position[1]),
                self.z_axis.steps_to_motor_position(grid_position[2]),
            ]
        )


ParamType = TypeVar("ParamType", bound=GridScanParamsCommon)


class ZebraGridScanParams(GridScanParamsCommon):
    """
    Params for standard Zebra FGS. Adds on the dwell time
    """

    dwell_time_ms: float = 10

    @field_validator("dwell_time_ms")
    @classmethod
    def non_integer_dwell_time(cls, dwell_time_ms: float) -> float:
        dwell_time_floor_rounded = np.floor(dwell_time_ms)
        dwell_time_is_close = np.isclose(
            dwell_time_ms, dwell_time_floor_rounded, rtol=1e-3
        )
        if not dwell_time_is_close:
            raise ValueError(
                f"Dwell time of {dwell_time_ms}ms is not an integer value. Fast Grid Scan only accepts integer values"
            )
        return dwell_time_ms


class PandAGridScanParams(GridScanParamsCommon):
    """
    Params for panda constant-motion scan. Adds on the goniometer run-up distance
    """

    run_up_distance_mm: float = 0.17


class MotionProgram(Device):
    def __init__(self, prefix: str, name: str = "") -> None:
        super().__init__(name)
        self.running = epics_signal_r(int, prefix + "PROGBITS")
        self.program_number = epics_signal_r(float, prefix + "CS1:PROG_NUM")


class FastGridScanCommon(StandardReadable, Flyable, ABC, Generic[ParamType]):
    """Device for a general fast grid scan

    When the motion program is started, the goniometer will move in a snake-like grid trajectory,
    with X as the fast axis and Y as the slow axis. If Z steps isn't 0, the goniometer will
    then rotate in the omega direction such that it moves from the X-Y, to the X-Z plane then
    do a second grid scan. The detector is triggered after every x step.
    See https://github.com/DiamondLightSource/hyperion/wiki/Coordinate-Systems for more
    """

    def __init__(self, prefix: str, smargon_prefix: str, name: str = "") -> None:
        self.x_steps = epics_signal_rw_rbv(int, f"{prefix}X_NUM_STEPS")
        self.y_steps = epics_signal_rw_rbv(
            int, f"{prefix}Y_NUM_STEPS"
        )  # Number of vertical steps during the first grid scan
        self.z_steps = epics_signal_rw_rbv(
            int, f"{prefix}Z_NUM_STEPS"
        )  # Number of vertical steps during the second grid scan, after the rotation in omega
        self.x_step_size = epics_signal_rw_rbv(float, f"{prefix}X_STEP_SIZE")
        self.y_step_size = epics_signal_rw_rbv(float, f"{prefix}Y_STEP_SIZE")
        self.z_step_size = epics_signal_rw_rbv(float, f"{prefix}Z_STEP_SIZE")
        self.x_start = epics_signal_rw_rbv(float, f"{prefix}X_START")
        self.y1_start = epics_signal_rw_rbv(float, f"{prefix}Y_START")
        self.y2_start = epics_signal_rw_rbv(float, f"{prefix}Y2_START")
        self.z1_start = epics_signal_rw_rbv(float, f"{prefix}Z_START")
        self.z2_start = epics_signal_rw_rbv(float, f"{prefix}Z2_START")

        self.scan_invalid = epics_signal_r(float, f"{prefix}SCAN_INVALID")

        self.run_cmd = epics_signal_x(f"{prefix}RUN.PROC")
        self.stop_cmd = epics_signal_x(f"{prefix}STOP.PROC")
        self.status = epics_signal_r(int, f"{prefix}SCAN_STATUS")

        self.expected_images = derived_signal_r(
            self._calculate_expected_images,
            x=self.x_steps,
            y=self.y_steps,
            z=self.z_steps,
        )

        self.motion_program = MotionProgram(smargon_prefix)

        self.position_counter = self._create_position_counter(prefix)

        # Kickoff timeout in seconds
        self.KICKOFF_TIMEOUT: float = 5.0

        self.COMPLETE_STATUS: float = 60.0

        self.movable_params: dict[str, Signal] = {
            "x_steps": self.x_steps,
            "y_steps": self.y_steps,
            "z_steps": self.z_steps,
            "x_step_size_mm": self.x_step_size,
            "y_step_size_mm": self.y_step_size,
            "z_step_size_mm": self.z_step_size,
            "x_start_mm": self.x_start,
            "y1_start_mm": self.y1_start,
            "y2_start_mm": self.y2_start,
            "z1_start_mm": self.z1_start,
            "z2_start_mm": self.z2_start,
        }
        super().__init__(name)

    def _calculate_expected_images(self, x: float, y: float, z: float) -> float:
        LOGGER.info(f"Reading num of images found {x, y, z} images in each axis")
        first_grid = x * y
        second_grid = x * z
        return first_grid + second_grid

    @AsyncStatus.wrap
    async def kickoff(self):
        curr_prog = await self.motion_program.program_number.get_value()
        running = await self.motion_program.running.get_value()
        if running:
            LOGGER.info(f"Motion program {curr_prog} still running, waiting...")
            await wait_for_value(self.motion_program.running, 0, self.KICKOFF_TIMEOUT)

        LOGGER.debug("Running scan")
        await self.run_cmd.trigger()
        LOGGER.info("Waiting for FGS to start")
        await wait_for_value(self.status, 1, self.KICKOFF_TIMEOUT)
        LOGGER.debug("FGS kicked off")

    @AsyncStatus.wrap
    async def complete(self):
        try:
            await wait_for_value(self.status, 0, self.COMPLETE_STATUS)
        except asyncio.TimeoutError:
            LOGGER.error(
                "Hyperion timed out waiting for FGS motion to complete. This may have been caused by a goniometer stage getting stuck.\n\
                Forcibly stopping the FGS motion program..."
            )
            await self.stop_cmd.trigger()
            raise

    @abstractmethod
    def _create_position_counter(self, prefix: str) -> SignalRW[int]:
        pass


class ZebraFastGridScan(FastGridScanCommon[ZebraGridScanParams]):
    """Device for standard Zebra FGS. In this scan, the goniometer's velocity profile follows a parabolic shape between X steps,
    with the slowest points occuring at each X step.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        full_prefix = prefix + "FGS:"
        # Time taken to travel between X steps
        self.dwell_time_ms = epics_signal_rw_rbv(float, f"{full_prefix}DWELL_TIME")

        self.x_counter = epics_signal_r(int, f"{full_prefix}X_COUNTER")
        self.y_counter = epics_signal_r(int, f"{full_prefix}Y_COUNTER")

        super().__init__(full_prefix, prefix, name)

        self.movable_params["dwell_time_ms"] = self.dwell_time_ms

    def _create_position_counter(self, prefix: str):
        return epics_signal_rw(
            int, f"{prefix}POS_COUNTER", write_pv=f"{prefix}POS_COUNTER_WRITE"
        )


class PandAFastGridScan(FastGridScanCommon[PandAGridScanParams]):
    """Device for panda constant-motion scan"""

    def __init__(self, prefix: str, name: str = "") -> None:
        full_prefix = prefix + "PGS:"
        self.time_between_x_steps_ms = (
            epics_signal_rw_rbv(  # Used by motion controller to set goniometer velocity
                float, f"{full_prefix}TIME_BETWEEN_X_STEPS"
            )
        )

        # Distance before and after the grid given to allow goniometer to reach desired speed while it is within the
        # grid
        self.run_up_distance_mm = epics_signal_rw_rbv(
            float, f"{full_prefix}RUNUP_DISTANCE"
        )
        super().__init__(full_prefix, prefix, name)

        self.movable_params["run_up_distance_mm"] = self.run_up_distance_mm

    def _create_position_counter(self, prefix: str):
        return epics_signal_rw(int, f"{prefix}Y_COUNTER")


def set_fast_grid_scan_params(scan: FastGridScanCommon[ParamType], params: ParamType):
    to_move = []

    # Create arguments for bps.mv
    for key in scan.movable_params.keys():
        to_move.extend([scan.movable_params[key], params.__dict__[key]])

    # Counter should always start at 0
    to_move.extend([scan.position_counter, 0])

    yield from mv(*to_move)
