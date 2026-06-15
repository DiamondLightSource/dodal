import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading

from dodal.common.enums import OnOffUpper
from dodal.devices.beamlines.i06_1 import DiffractionDichroism


@pytest.fixture
def dd() -> DiffractionDichroism:
    with init_devices(mock=True):
        dd = DiffractionDichroism("TEST:")
    return dd


async def test_dd_read(dd: DiffractionDichroism) -> None:
    await assert_reading(
        dd,
        {
            "dd-x": partial_reading(0),
            "dd-y": partial_reading(0),
            "dd-z": partial_reading(0),
            "dd-theta": partial_reading(0),
            "dd-chi": partial_reading(0),
            "dd-phi": partial_reading(0),
            "dd-twotheta": partial_reading(0),
            "dd-dy": partial_reading(0),
            "dd-cl1-intensity": partial_reading(0),
            "dd-cl1-switch": partial_reading(OnOffUpper.ON),
            "dd-cl2-intensity": partial_reading(0),
            "dd-cl2-switch": partial_reading(OnOffUpper.ON),
            "dd-cl3-intensity": partial_reading(0),
            "dd-cl3-switch": partial_reading(OnOffUpper.ON),
            "dd-cl4-intensity": partial_reading(0),
            "dd-cl4-switch": partial_reading(OnOffUpper.ON),
            "dd-cl5-intensity": partial_reading(0),
            "dd-cl5-switch": partial_reading(OnOffUpper.ON),
        },
    )
