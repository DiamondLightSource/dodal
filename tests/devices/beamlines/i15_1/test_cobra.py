from daq_config_server import ConfigClient
from daq_config_server.models.i15_1.xpdf_parameters import (
    TemperatureControllerParams,
)

from dodal.devices.beamlines.i15_1.cobra import Cobra
from tests.test_data import TEST_XPDF_LOCAL_PARAMETERS


def test_cobra_config_client_reads_config_file_successfully():
    cobra = Cobra("", ConfigClient(""), TEST_XPDF_LOCAL_PARAMETERS)
    assert cobra.get_config() == TemperatureControllerParams(
        beam_position=461.5,
        safe_position=2.0,
        settle_time=600,
        tolerance=5.0,
        units="K",
        ramp_units="/h",
        use_calibration=True,
        use_fast_cool=True,
        calibration_file="cobra_calibration_2025-09-11.txt",
    )
