from unittest.mock import MagicMock

import pytest
from ophyd_async.core import init_devices

from dodal.devices.aperture import Aperture
from dodal.devices.util.adjuster_plans import lookup_table_adjuster


@pytest.fixture
async def fake_aperture():
    with init_devices(mock=True):
        fake_aperture = Aperture(prefix="test_ap", name="aperture")
    return fake_aperture


def test_lookup_table_adjuster(fake_aperture):
    lookup = MagicMock(return_value=4.1)
    output_device = fake_aperture.y
    plan = lookup_table_adjuster(lookup, output_device, 2)("TEST_GROUP")
    messages = list(plan)
    assert len(messages) == 1
    msg = messages[0]
    assert msg.command == "set"
    assert msg.args == (4.1,)
    assert msg.kwargs["group"] == "TEST_GROUP"
