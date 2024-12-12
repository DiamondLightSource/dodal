import bluesky.plan_stubs as bps
import pytest

from dodal.devices.i24.focus_mirrors import FocusMirrorsMode, HFocusMode, VFocusMode


@pytest.fixture
async def fake_mirrors(RE) -> FocusMirrorsMode:
    mirrors = FocusMirrorsMode("", name="fake_morrors")
    await mirrors.connect(mock=True)

    return mirrors


async def test_setting_mirror_focus_returns_correct_beam_size(
    fake_mirrors: FocusMirrorsMode, RE
):
    def set_mirrors():
        yield from bps.abs_set(
            fake_mirrors.horizontal, HFocusMode.FOCUS_3010D, wait=True
        )
        yield from bps.abs_set(fake_mirrors.vertical, VFocusMode.FOCUS_3010D, wait=True)

    RE(set_mirrors())

    assert await fake_mirrors.beam_size_x.get_value() == 30
    assert await fake_mirrors.beam_size_y.get_value() == 10
