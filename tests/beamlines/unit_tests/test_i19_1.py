import sys
from unittest.mock import patch

from bluesky.protocols import HasName
from ophyd import Device, EpicsMotor

with patch.dict("os.environ", {"BEAMLINE": "i19_1"}, clear=True):
    from dodal.beamlines import beamline_utils, i19_1
    from dodal.utils import make_all_devices


def teardown_module() -> None:
    beamline_utils.BL = "i19_1"
    for module in list(sys.modules):
        if module.endswith("beamline_utils"):
            del sys.modules[module]


def given_the_device_with_key(key: str) -> Device:
    i19_1_devices: dict[str, Device] = beamline_utils.ACTIVE_DEVICES
    return i19_1_devices[key]


def test_i19_1_has_at_least_one_device_created() -> None:
    active_i19_1_devices: dict[str, HasName] = make_all_devices(
        i19_1, fake_with_ophyd_sim=True
    )
    assert len(active_i19_1_devices) > 0


def test_i19_1_has_active_diffractomer() -> None:
    diffractometer_key: str = "eh1_diffractometer"
    active_i19_1_devices: dict[str, HasName] = make_all_devices(
        i19_1, fake_with_ophyd_sim=True
    )
    _verify_inclusion_amongst_active_devices(
        expected_key=diffractometer_key, active_devices=active_i19_1_devices
    )


def test_i19_1_has_active_off_axis_viewer() -> None:
    off_axis_viewer_key: str = "oav2"
    active_i19_1_devices: dict[str, HasName] = make_all_devices(
        i19_1, fake_with_ophyd_sim=True
    )
    _verify_inclusion_amongst_active_devices(
        expected_key=off_axis_viewer_key, active_devices=active_i19_1_devices
    )


def test_i19_1_has_active_on_axis_viewer() -> None:
    on_axis_viewer_key: str = "oav1"
    active_i19_1_devices: dict[str, HasName] = make_all_devices(
        i19_1, fake_with_ophyd_sim=True
    )
    _verify_inclusion_amongst_active_devices(
        expected_key=on_axis_viewer_key, active_devices=active_i19_1_devices
    )


def test_i19_1_diffractometer_x_has_expected_pv() -> None:
    diffractometer_key: str = "eh1_diffractometer"
    diffractometer: Device = given_the_device_with_key(diffractometer_key)
    x_motor = diffractometer.centre_x
    expected_x_motor_pv_prefix = "BL19I-MO-CENT-01:X"
    _verify_pv_prefix_of_motor(expected_x_motor_pv_prefix, x_motor)


def test_i19_1_diffractometer_y_has_expected_pv() -> None:
    diffractometer_key: str = "eh1_diffractometer"
    diffractometer: Device = given_the_device_with_key(diffractometer_key)
    y_motor = diffractometer.centre_y
    expected_y_motor_pv_prefix = "BL19I-MO-CENT-01:Y"
    _verify_pv_prefix_of_motor(expected_y_motor_pv_prefix, y_motor)


def test_i19_1_diffractometer_z_has_expected_pv() -> None:
    diffractometer_key: str = "eh1_diffractometer"
    diffractometer: Device = given_the_device_with_key(diffractometer_key)
    z_motor = diffractometer.centre_z
    expected_z_motor_pv_prefix = "BL19I-MO-CENT-01:Z"
    _verify_pv_prefix_of_motor(expected_z_motor_pv_prefix, z_motor)


def test_i19_1_diffractometer_phi_has_expected_pv() -> None:
    diffractometer_key: str = "eh1_diffractometer"
    diffractometer: Device = given_the_device_with_key(diffractometer_key)
    phi_motor = diffractometer.phi
    expected_phi_motor_pv_prefix = "BL19I-MO-GONIO-02:PHI"
    _verify_pv_prefix_of_motor(expected_phi_motor_pv_prefix, phi_motor)


def test_i19_1_diffractometer_omega_has_expected_pv() -> None:
    diffractometer_key: str = "eh1_diffractometer"
    diffractometer: Device = given_the_device_with_key(diffractometer_key)
    omega_motor = diffractometer.omega
    expected_omega_motor_pv_prefix = "BL19I-MO-GONIO-01:OMEGA"
    _verify_pv_prefix_of_motor(expected_omega_motor_pv_prefix, omega_motor)


def test_i19_1_diffractometer_two_theta_has_expected_pv() -> None:
    diffractometer_key: str = "eh1_diffractometer"
    diffractometer: Device = given_the_device_with_key(diffractometer_key)
    omega_motor = diffractometer.two_theta
    expected_omega_motor_pv_prefix = "BL19I-MO-GONIO-03:2THETA"
    _verify_pv_prefix_of_motor(expected_omega_motor_pv_prefix, omega_motor)


def test_i19_1_diffractometer_detector_distance_has_expected_pv() -> None:
    diffractometer_key: str = "eh1_diffractometer"
    diffractometer: Device = given_the_device_with_key(diffractometer_key)
    detector_distance: EpicsMotor = diffractometer.detector_distance
    expected_det_motor_pv_prefix: str = "BL19I-MO-GONIO-03:DET"
    _verify_pv_prefix_of_motor(expected_det_motor_pv_prefix, detector_distance)


def _verify_inclusion_amongst_active_devices(
    expected_key: str, active_devices: dict[str, Device]
) -> None:
    assert expected_key in active_devices.keys()


def _verify_pv_prefix_of_motor(expected_pv: str, motor: EpicsMotor) -> None:
    assert motor.prefix == expected_pv
