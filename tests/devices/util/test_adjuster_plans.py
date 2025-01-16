from unittest.mock import MagicMock

import pytest
from ophyd.sim import make_fake_device

from dodal.devices.aperture import Aperture
from dodal.devices.util.adjuster_plans import lookup_table_adjuster


@pytest.fixture
def fake_aperture():
    FakeAperture = make_fake_device(Aperture)
    fake_aperture: Aperture = FakeAperture(prefix="", name="aperture")
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
