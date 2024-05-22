from functools import partial
from typing import Any, Mapping
from unittest.mock import MagicMock, patch

from ophyd.epics_motor import EpicsMotor
from ophyd.status import Status
from ophyd_async.core import (
    StandardReadable,
    callback_on_mock_put,
    set_mock_value,
)
from ophyd_async.epics.motion import Motor

from dodal.devices.detector.det_dim_constants import constants_from_type
from dodal.devices.detector.det_dist_to_beam_converter import (
    DetectorDistanceToBeamXYConverter,
)
from dodal.devices.detector.detector import DetectorParams
from dodal.devices.smargon import Smargon
from dodal.testing_utils import constants


async def assert_reading(
    device: StandardReadable,
    expected_reading: Mapping[str, Any],
) -> None:
    reading = await device.read()

    assert reading == expected_reading


def mock_beamline_module_filepaths(bl_name, bl_module):
    if mock_attributes := constants.MOCK_ATTRIBUTES_TABLE.get(bl_name):
        [bl_module.__setattr__(attr[0], attr[1]) for attr in mock_attributes]


def set_smargon_pos(smargon: Smargon, pos: tuple[float, float, float]):
    smargon.x.user_readback.sim_put(pos[0])  # type: ignore
    smargon.y.user_readback.sim_put(pos[1])  # type: ignore
    smargon.z.user_readback.sim_put(pos[2])  # type: ignore


def patch_ophyd_async_motor(
    motor: Motor, initial_position=0, call_log: MagicMock | None = None
):
    """Set some sane defaults, and add a callback to propagate puts to the readback.
    If passed a mock object for call_log, it will call it for all calls to the
    setpoint - useful for testing the order multiple motors are set in.
    """

    def _pass_on_mock(motor, call_log: MagicMock | None = None):
        def _pass_on_mock(value, **kwargs):
            set_mock_value(motor.user_readback, value)
            if call_log is not None:
                call_log(value, **kwargs)

        return _pass_on_mock

    set_mock_value(motor.user_setpoint, initial_position)
    set_mock_value(motor.user_readback, initial_position)
    set_mock_value(motor.deadband, 0.001)
    set_mock_value(motor.motor_done_move, 1)
    return callback_on_mock_put(motor.user_setpoint, _pass_on_mock(motor, call_log))


def patch_ophyd_motor(motor: EpicsMotor, initial_position=0):
    def mock_set(motor: EpicsMotor, val):
        motor.user_setpoint.sim_put(val)  # type: ignore
        motor.user_readback.sim_put(val)  # type: ignore
        return Status(done=True, success=True)

    motor.user_setpoint.sim_put(initial_position)  # type: ignore
    motor.user_readback.sim_put(initial_position)  # type: ignore
    return patch.object(motor, "set", MagicMock(side_effect=partial(mock_set, motor)))


class StatusException(Exception):
    pass


def get_bad_status(exception=StatusException):
    status = Status()
    status.set_exception(exception)
    return status


def create_new_detector_params(
    *,
    directory=constants.EIGER_DIR,
    det_dist_path=constants.EIGER_DET_DIST_TO_BEAM_CONVERTER_PATH,
    run_number: int | None = constants.EIGER_RUN_NUMBER,
) -> DetectorParams:
    extra_params = {}
    if run_number is not None:
        extra_params["run_number"] = run_number
    return DetectorParams(
        expected_energy_ev=constants.EIGER_EXPECTED_ENERGY,
        exposure_time=constants.EIGER_EXPOSURE_TIME,
        directory=directory,
        prefix=constants.EIGER_PREFIX,
        detector_distance=constants.EIGER_DETECTOR_DISTANCE,
        omega_start=constants.EIGER_OMEGA_START,
        omega_increment=constants.EIGER_OMEGA_INCREMENT,
        num_images_per_trigger=constants.EIGER_NUM_IMAGES_PER_TRIGGER,
        num_triggers=constants.EIGER_NUM_TRIGGERS,
        use_roi_mode=constants.EIGER_USE_ROI_MODE,
        det_dist_to_beam_converter_path=det_dist_path,
        detector_size_constants=constants_from_type(
            constants.EIGER_DETECTOR_SIZE_CONSTANTS.det_type_string
        ),
        beam_xy_converter=DetectorDistanceToBeamXYConverter(
            constants.EIGER_DET_DIST_TO_BEAM_CONVERTER_PATH
        ),
        **extra_params,
    )
