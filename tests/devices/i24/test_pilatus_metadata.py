import bluesky.plan_stubs as bps
import pytest
from ophyd_async.testing import set_mock_value

from dodal.devices.i24.pilatus_metadata import PilatusMetadata


@pytest.fixture
async def fake_pilatus(RE) -> PilatusMetadata:
    pilatus = PilatusMetadata("", name="fake_pilatus")
    await pilatus.connect(mock=True)

    set_mock_value(pilatus.template, "%s%s%05d.cbf")
    set_mock_value(pilatus.filenumber, 10)

    return pilatus


async def test_set_filename_and_get_full_template(fake_pilatus, RE):
    expected_template = "test_00010_#####.cbf"

    RE(bps.abs_set(fake_pilatus.filename, "test_", wait=True))

    assert await fake_pilatus.filename_template.get_value() == expected_template
