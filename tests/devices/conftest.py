import asyncio

import pytest
from ophyd_async.core import init_devices

from dodal.common.beamlines.beamline_parameters import GDABeamlineParameters
from dodal.devices.aperturescatterguard import (
    AperturePosition,
    ApertureScatterguard,
    ApertureValue,
    load_positions_from_beamline_parameters,
)


@pytest.fixture
def aperture_positions() -> dict[ApertureValue, AperturePosition]:
    return load_positions_from_beamline_parameters(
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
    aperture_positions: dict[ApertureValue, AperturePosition],
    aperture_tolerances: AperturePosition,
) -> ApertureScatterguard:
    async with init_devices(mock=True):
        ap_sg = ApertureScatterguard(
            aperture_prefix="-MO-MAPT-01:",
            scatterguard_prefix="-MO-SCAT-01:",
            name="test_ap_sg",
            loaded_positions=aperture_positions,
            tolerances=aperture_tolerances,
        )
    return ap_sg


async def set_to_position(
    aperture_scatterguard: ApertureScatterguard, position: AperturePosition
):
    aperture_x, aperture_y, aperture_z, scatterguard_x, scatterguard_y = position.values

    await asyncio.gather(
        aperture_scatterguard.aperture.x.set(aperture_x),
        aperture_scatterguard.aperture.y.set(aperture_y),
        aperture_scatterguard.aperture.z.set(aperture_z),
        aperture_scatterguard.scatterguard.x.set(scatterguard_x),
        aperture_scatterguard.scatterguard.y.set(scatterguard_y),
    )
