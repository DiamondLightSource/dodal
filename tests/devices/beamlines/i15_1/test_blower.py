from daq_config_server import ConfigClient
from daq_config_server.models.i15_1.xpdf_parameters import (
    TemperatureControllerParams,
)

from dodal.devices.beamlines.i15_1.blower import Blower
from tests.test_data import TEST_XPDF_LOCAL_PARAMETERS


def test_blower_config_client_reads_config_file_successfully():
    blower = Blower("", ConfigClient(""), TEST_XPDF_LOCAL_PARAMETERS)
    assert blower.get_config() == TemperatureControllerParams(
        beam_position=44.7,
        safe_position=2.0,
        settle_time=0,
        tolerance=5.0,
        units="C",
        ramp_units="/min",
        use_calibration=True,
        use_fast_cool=None,
        calibration_file="blower_cal_10_03_2026.txt",
    )
