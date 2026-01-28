from os import environ
from unittest.mock import patch

import pytest

from dodal.common.beamlines.beamline_parameters import (
    get_beamline_parameters,
)
from tests.test_data import (
    I04_BEAMLINE_PARAMETERS,
    TEST_BEAMLINE_PARAMETERS_TXT,
)

BL = "i03"


def test_beamline_parameters():
    params = get_beamline_parameters(BL, TEST_BEAMLINE_PARAMETERS_TXT)
    assert params["sg_x_MEDIUM_APERTURE"] == 5.285
    assert params["col_parked_downstream_x"] == 0
    assert params["beamLineEnergy__pitchStep"] == 0.002
    assert params["DataCollection_TurboMode"] is True
    assert params["beamLineEnergy__adjustSlits"] is False


def test_i03_beamline_parameters():
    params = get_beamline_parameters(BL, I04_BEAMLINE_PARAMETERS)
    assert params["flux_predict_polynomial_coefficients_5"] == [
        -0.0000707134131045123,
        7.0205491504418,
        -194299.6440518530,
        1835805807.3974800,
        -3280251055671.100,
    ]


def test_get_beamline_parameters_works_with_no_environment_variable_set():
    if environ.get("BEAMLINE"):
        del environ["BEAMLINE"]
    assert get_beamline_parameters(BL)


def test_get_beamline_parameters():
    with patch.dict(
        "dodal.common.beamlines.beamline_parameters.BEAMLINE_PARAMETER_PATHS",
        {"i03": TEST_BEAMLINE_PARAMETERS_TXT},
    ):
        params = get_beamline_parameters("i03")
    assert params["col_parked_downstream_x"] == 0
    assert params["BackStopZyag"] == 19.1
    assert params["store_data_collections_in_ispyb"] is True
    assert params["attenuation_optimisation_type"] == "deadtime"


@pytest.fixture(autouse=True)
def i03_beamline_parameters():
    with patch.dict(
        "dodal.common.beamlines.beamline_parameters.BEAMLINE_PARAMETER_PATHS",
        {"i03": TEST_BEAMLINE_PARAMETERS_TXT},
    ) as params:
        yield params
