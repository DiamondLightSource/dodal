import asyncio

import pytest
from ophyd_async.core import get_mock_put, init_devices

from dodal.common.beamlines.beamline_parameters import GDABeamlineParameters
from dodal.devices.mx_phase1.aperturescatterguard import (
    AperturePosition,
    ApertureScatterguard,
    ApertureScatterguardConfiguration,
    load_configuration,
)


@pytest.fixture
def ap_sg_configuration() -> ApertureScatterguardConfiguration:
    return load_configuration(
        GDABeamlineParameters(
            params={
                "miniap_x_LARGE_APERTURE": 2.389,
                "miniap_y_LARGE_APERTURE": 40.986,
                "miniap_z_LARGE_APERTURE": 15.8,
                "sg_x_LARGE_APERTURE": 5.25,
                "sg_y_LARGE_APERTURE": 4.43,
                "miniap_x_MEDIUM_APERTURE": 2.384,
                "miniap_y_MEDIUM_APERTURE": 44.967,
                "miniap_z_MEDIUM_APERTURE": 15.8,
                "sg_x_MEDIUM_APERTURE": 5.285,
                "sg_y_MEDIUM_APERTURE": 0.46,
                "miniap_x_SMALL_APERTURE": 2.430,
                "miniap_y_SMALL_APERTURE": 48.974,
                "miniap_z_SMALL_APERTURE": 15.8,
                "sg_x_SMALL_APERTURE": 5.3375,
                "sg_y_SMALL_APERTURE": -3.55,
                "miniap_x_ROBOT_LOAD": 2.386,
                "miniap_y_ROBOT_LOAD": 31.40,
                "miniap_z_ROBOT_LOAD": 15.8,
                "sg_x_ROBOT_LOAD": 5.25,
                "sg_y_ROBOT_LOAD": 4.43,
                "miniap_x_MANUAL_LOAD": -4.91,
                "miniap_y_MANUAL_LOAD": -48.70,
                "miniap_z_MANUAL_LOAD": -10.0,
                "sg_x_MANUAL_LOAD": -4.7,
                "sg_y_MANUAL_LOAD": 1.8,
                "miniap_x_SCIN_MOVE": -4.91,
                "sg_x_SCIN_MOVE": -4.75,
            }
        )
    )


@pytest.fixture
def aperture_tolerances():
    return AperturePosition.tolerances_from_gda_params(
        GDABeamlineParameters(
            {
                "miniap_x_tolerance": 0.004,
                "miniap_y_tolerance": 0.1,
                "miniap_z_tolerance": 0.1,
                "sg_x_tolerance": 0.1,
                "sg_y_tolerance": 0.1,
            }
        )
    )


@pytest.fixture
async def ap_sg(
    ap_sg_configuration: ApertureScatterguardConfiguration,
    aperture_tolerances: AperturePosition,
) -> ApertureScatterguard:
    async with init_devices(mock=True):
        ap_sg = ApertureScatterguard(
            aperture_prefix="-MO-MAPT-01:",
            scatterguard_prefix="-MO-SCAT-01:",
            name="test_ap_sg",
            config=ap_sg_configuration,
            tolerances=aperture_tolerances,
        )
    return ap_sg


async def set_to_position(
    aperture_scatterguard: ApertureScatterguard, position: AperturePosition
):
    aperture_x, aperture_y, aperture_z, scatterguard_x, scatterguard_y = position.values

    motors = [
        aperture_scatterguard.aperture.x,
        aperture_scatterguard.aperture.y,
        aperture_scatterguard.aperture.z,
        aperture_scatterguard.scatterguard.x,
        aperture_scatterguard.scatterguard.y,
    ]
    await asyncio.gather(
        *[m.set(value) for m, value in zip(motors, position.values, strict=True)]
    )
    for signal in [m.user_setpoint for m in motors]:
        get_mock_put(signal).reset_mock()
