from unittest.mock import ANY

from ophyd_async.core import set_mock_value

from dodal.devices.slits import Slits
from dodal.testing_utils import assert_reading


async def test_reading_slits_reads_gaps_and_centres(mock_slits: Slits):
    set_mock_value(mock_slits.x_gap.user_readback, 0.5)
    set_mock_value(mock_slits.y_centre.user_readback, 1.0)
    set_mock_value(mock_slits.y_gap.user_readback, 1.5)

    await assert_reading(
        mock_slits,
        {
            "slits-x_centre": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 0.0,
            },
            "slits-x_gap": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 0.5,
            },
            "slits-y_centre": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 1.0,
            },
            "slits-y_gap": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 1.5,
            },
        },
    )
