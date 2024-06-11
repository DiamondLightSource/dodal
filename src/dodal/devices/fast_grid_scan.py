from abc import ABC
from typing import Any, Generic, TypeVar

import numpy as np
from bluesky.plan_stubs import mv
from numpy import ndarray
from ophyd_async.core import (
    AsyncStatus,
    Device,
    Signal,
    SignalR,
    SoftSignalBackend,
    StandardReadable,
    wait_for_value,
)
from ophyd_async.epics.signal import (
    epics_signal_r,
    epics_signal_rw,
)
from ophyd_async.epics.signal.signal import epics_signal_rw_rbv
from pydantic import validator
from pydantic.dataclasses import dataclass

from dodal.devices.motors import XYZLimitBundle
from dodal.log import LOGGER
from dodal.parameters.experiment_parameter_base import AbstractExperimentWithBeamParams


@dataclass
class GridAxis:
    start: float
    step_size: float
    full_steps: int

    def steps_to_motor_position(self, steps):
        """Gives the motor position based on steps, where steps are 0 indexed"""
        return self.start + self.step_size * steps

    @property
    def end(self):
        """Gives the point where the final frame is taken"""
        # Note that full_steps is one indexed e.g. if there is one step then the end is
        # refering to the first position
        return self.steps_to_motor_position(self.full_steps - 1)

    def is_within(self, steps):
        return 0 <= steps <= self.full_steps


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
    x_step_size: float = 0.1
    y_step_size: float = 0.1
    z_step_size: float = 0.1
    x_start: float = 0.1
    y1_start: float = 0.1
    y2_start: float = 0.1
    z1_start: float = 0.1
    z2_start: float = 0.1
    x_axis: GridAxis = GridAxis(0, 0, 0)
    y_axis: GridAxis = GridAxis(0, 0, 0)
    z_axis: GridAxis = GridAxis(0, 0, 0)

    # Whether to set the stub offsets after centering
    set_stub_offsets: bool = False

    def get_param_positions(self) -> dict:
        return {
            "x_steps": self.x_steps,
            "y_steps": self.y_steps,
            "z_steps": self.z_steps,
            "x_step_size": self.x_step_size,
            "y_step_size": self.y_step_size,
            "z_step_size": self.z_step_size,
            "x_start": self.x_start,
            "y1_start": self.y1_start,
            "y2_start": self.y2_start,
            "z1_start": self.z1_start,
            "z2_start": self.z2_start,
        }

    class Config:
        arbitrary_types_allowed = True
        fields = {
            "x_axis": {"exclude": True},
            "y_axis": {"exclude": True},
            "z_axis": {"exclude": True},
        }

    @validator("x_axis", always=True)
    def _get_x_axis(cls, x_axis: GridAxis, values: dict[str, Any]) -> GridAxis:
        return GridAxis(values["x_start"], values["x_step_size"], values["x_steps"])

    @validator("y_axis", always=True)
    def _get_y_axis(cls, y_axis: GridAxis, values: dict[str, Any]) -> GridAxis:
        return GridAxis(values["y1_start"], values["y_step_size"], values["y_steps"])

    @validator("z_axis", always=True)
    def _get_z_axis(cls, z_axis: GridAxis, values: dict[str, Any]) -> GridAxis:
        return GridAxis(values["z2_start"], values["z_step_size"], values["z_steps"])

    def is_valid(self, limits: XYZLimitBundle) -> bool:
        """
        Validates scan parameters

        :param limits: The motor limits against which to validate
                       the parameters
        :return: True if the scan is valid
        """
        x_in_limits = limits.x.is_within(self.x_axis.start) and limits.x.is_within(
            self.x_axis.end
        )
        y_in_limits = limits.y.is_within(self.y_axis.start) and limits.y.is_within(
            self.y_axis.end
        )

        first_grid_in_limits = (
            x_in_limits and y_in_limits and limits.z.is_within(self.z1_start)
        )

        z_in_limits = limits.z.is_within(self.z_axis.start) and limits.z.is_within(
            self.z_axis.end
        )

        second_grid_in_limits = (
            x_in_limits and z_in_limits and limits.y.is_within(self.y2_start)
        )

        return first_grid_in_limits and second_grid_in_limits

    def get_num_images(self):
        return self.x_steps * self.y_steps + self.x_steps * self.z_steps

    @property
    def is_3d_grid_scan(self):
        return self.z_steps > 0

    def grid_position_to_motor_position(self, grid_position: ndarray) -> ndarray:
        """Converts a grid position, given as steps in the x, y, z grid,
        to a real motor position.

        :param grid_position: The x, y, z position in grid steps
        :return: The motor position this corresponds to.
        :raises: IndexError if the desired position is outside the grid."""
        for position, axis in zip(
            grid_position, [self.x_axis, self.y_axis, self.z_axis]
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

    def get_param_positions(self):
        param_positions = super().get_param_positions()
        param_positions["dwell_time_ms"] = self.dwell_time_ms
        return param_positions

    @validator("dwell_time_ms", always=True, check_fields=True)
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

    def get_param_positions(self):
        param_positions = super().get_param_positions()
        param_positions["run_up_distance_mm"] = self.run_up_distance_mm
        return param_positions


class MotionProgram(Device):
    def __init__(self, prefix: str, name: str = "") -> None:
        super().__init__(name)
        self.running = epics_signal_r(float, prefix + "PROGBITS")
        self.program_number = epics_signal_r(float, prefix + "CS1:PROG_NUM")


class ExpectedImages(SignalR[int]):
    def __init__(self, parent: "FastGridScanCommon") -> None:
        super().__init__(SoftSignalBackend(int))
        self.parent: "FastGridScanCommon" = parent

    async def get_value(self):
        x = await self.parent.x_steps.get_value()
        y = await self.parent.y_steps.get_value()
        z = await self.parent.z_steps.get_value()
        first_grid = x * y
        second_grid = x * z
        return first_grid + second_grid


class FastGridScanCommon(StandardReadable, ABC, Generic[ParamType]):
    """Device for a general fast grid scan

    When the motion program is started, the goniometer will move in a snake-like grid trajectory,
    with X as the fast axis and Y as the slow axis. If Z steps isn't 0, the goniometer will
    then rotate in the omega direction such that it moves from the X-Y, to the X-Z plane then
    do a second grid scan. The detector is triggered after every x step.
    See https://github.com/DiamondLightSource/hyperion/wiki/Coordinate-Systems for more
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        super().__init__(name)
        self.x_steps = epics_signal_rw_rbv(int, "X_NUM_STEPS")
        self.y_steps = epics_signal_rw_rbv(
            int, "X_NUM_STEPS"
        )  # Number of vertical steps during the first grid scan
        self.z_steps = epics_signal_rw_rbv(
            int, "X_NUM_STEPS"
        )  # Number of vertical steps during the second grid scan, after the rotation in omega
        self.x_step_size = epics_signal_rw_rbv(float, "X_STEP_SIZE")
        self.y_step_size = epics_signal_rw_rbv(float, "Y_STEP_SIZE")
        self.z_step_size = epics_signal_rw_rbv(float, "Z_STEP_SIZE")
        self.x_start = epics_signal_rw_rbv(float, "X_START")
        self.y1_start = epics_signal_rw_rbv(float, "Y_START")
        self.y2_start = epics_signal_rw_rbv(float, "Y2_START")
        self.z1_start = epics_signal_rw_rbv(float, "Z_START")
        self.z2_start = epics_signal_rw_rbv(float, "Z2_START")

        self.position_counter = epics_signal_rw(
            int, "POS_COUNTER", write_pv="POS_COUNTER_WRITE"
        )
        self.x_counter = epics_signal_r(int, "X_COUNTER")
        self.y_counter = epics_signal_r(int, "Y_COUNTER")
        self.scan_invalid = epics_signal_r(float, "SCAN_INVALID")

        self.run_cmd = epics_signal_rw(int, "RUN.PROC")
        self.stop_cmd = epics_signal_rw(int, "STOP.PROC")
        self.status = epics_signal_r(float, "SCAN_STATUS")

        self.expected_images = ExpectedImages(parent=self)

        self.motion_program = MotionProgram(prefix)

        # Kickoff timeout in seconds
        self.KICKOFF_TIMEOUT: float = 5.0

        self.COMPLETE_STATUS: float = 60.0

        self.movable_params: dict[str, Signal] = {
            "x_steps": self.x_steps,
            "y_steps": self.y_steps,
            "z_steps": self.z_steps,
            "x_step_size": self.x_step_size,
            "y_step_size": self.y_step_size,
            "z_step_size": self.z_step_size,
            "x_start": self.x_start,
            "y1_start": self.y1_start,
            "y2_start": self.y2_start,
            "z1_start": self.z1_start,
            "z2_start": self.z2_start,
        }

    @AsyncStatus.wrap
    async def kickoff(self):
        curr_prog = await self.motion_program.program_number.get_value()
        running = await self.motion_program.running.get_value()
        if running:
            LOGGER.info(f"Motion program {curr_prog} still running, waiting...")
            await wait_for_value(self.motion_program.running, 0, self.KICKOFF_TIMEOUT)

        LOGGER.debug("Running scan")
        await self.run_cmd.set(1)
        LOGGER.info("Waiting for FGS to start")
        await wait_for_value(self.status, 1, self.KICKOFF_TIMEOUT)
        LOGGER.debug("FGS kicked off")

    @AsyncStatus.wrap
    async def complete(self):
        await wait_for_value(self.status, 0, self.COMPLETE_STATUS)


class ZebraFastGridScan(FastGridScanCommon[ZebraGridScanParams]):
    """Device for standard Zebra FGS. In this scan, the goniometer's velocity profile follows a parabolic shape between X steps,
    with the slowest points occuring at each X step.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        super().__init__(prefix, name)

        # Time taken to travel between X steps
        self.dwell_time_ms = epics_signal_rw_rbv(float, "DWELL_TIME")
        self.movable_params["dwell_time_ms"] = self.dwell_time_ms


class PandAFastGridScan(FastGridScanCommon[PandAGridScanParams]):
    """Device for panda constant-motion scan"""

    def __init__(self, prefix: str, name: str = "") -> None:
        super().__init__(prefix, name)
        self.time_between_x_steps_ms = (
            epics_signal_rw_rbv(  # Used by motion controller to set goniometer velocity
                float, "TIME_BETWEEN_X_STEPS"
            )
        )

        # Distance before and after the grid given to allow goniometer to reach desired speed while it is within the
        # grid
        self.run_up_distance_mm = epics_signal_rw_rbv(float, "RUNUP_DISTANCE")
        self.movable_params["run_up_distance_mm"] = self.run_up_distance_mm


def set_fast_grid_scan_params(scan: FastGridScanCommon[ParamType], params: ParamType):
    to_move = []

    # Create arguments for bps.mv
    for key in scan.movable_params.keys():
        to_move.extend([scan.movable_params[key], params.__dict__[key]])

    # Counter should always start at 0
    to_move.extend([scan.position_counter, 0])

    yield from mv(*to_move)
