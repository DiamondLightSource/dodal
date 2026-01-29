from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.i10_1 import ElectromagnetMagnetField


async def test_electronmagnet_magnet_field_read():
    with init_devices(mock=True):
        mock_em_field = ElectromagnetMagnetField(prefix="BLXX-EA-EMAG-01:")
    await assert_reading(
        mock_em_field,
        {
            "mock_em_field-field": partial_reading(0.0),
            "mock_em_field-current": partial_reading(0.0),
        },
    )
