import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.beamlines.i06_2 import PEEMManipulator


@pytest.fixture
def peem() -> PEEMManipulator:
    with init_devices(mock=True):
        peem = PEEMManipulator("TEST:")
    return peem


async def test_peem_read(peem: PEEMManipulator) -> None:
    await assert_reading(
        peem,
        {
            "peem-x": partial_reading(0),
            "peem-y": partial_reading(0),
            "peem-phi": partial_reading(0),
            "peem-es": partial_reading(0),
        },
    )
