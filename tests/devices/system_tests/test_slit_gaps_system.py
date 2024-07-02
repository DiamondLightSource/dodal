import pytest

from dodal.devices.slits import Slits


@pytest.mark.s03
async def test_when_s4_slit_gaps_created_against_s03_then_can_connect():
    slit_gaps = Slits("BL03S-AL-SLITS-04:", name="slit_gaps")

    await slit_gaps.connect()
