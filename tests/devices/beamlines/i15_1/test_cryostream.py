from daq_config_server import ConfigClient
from daq_config_server.models.i15_1.xpdf_parameters import (
    TemperatureControllerParams,
)

from dodal.devices.beamlines.i15_1.cryostream import Cryostream
from tests.test_data import TEST_XPDF_LOCAL_PARAMETERS


def test_cryostream_config_client_reads_config_file_successfully():
    cryostream = Cryostream("", ConfigClient(""), TEST_XPDF_LOCAL_PARAMETERS)
    assert cryostream.get_config() == TemperatureControllerParams(
        beam_position=469.9,
        safe_position=0.0,
        settle_time=600,
        tolerance=0.5,
        units="K",
        ramp_units="/h",
        use_calibration=True,
        use_fast_cool=None,
        calibration_file="cryostream_cal_2025-01-23.txt",
    )
