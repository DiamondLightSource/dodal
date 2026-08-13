import pytest

from dodal.devices.beamlines.i06_1.magnet import MagnetMode


@pytest.mark.parametrize(
    "mode, expected_alias",
    [
        (MagnetMode.UNIAXIAL_X, "x"),
        (MagnetMode.UNIAXIAL_Y, "y"),
        (MagnetMode.UNIAXIAL_Z, "z"),
    ],
)
def test_magnet_mode_axis_alias(mode: MagnetMode, expected_alias: str) -> None:
    assert mode.axis_alias == expected_alias


@pytest.mark.parametrize(
    "mode",
    [
        MagnetMode.CUBIC,
        MagnetMode.PLANAR_XZ,
        MagnetMode.QUADRANT_XY,
        MagnetMode.SPHERICAL,
        MagnetMode.UNDEFINED,
    ],
)
def test_magnet_mode_axis_alias_raises_error_when_not_axis(mode: MagnetMode) -> None:
    with pytest.raises(ValueError):
        mode.axis_alias  # noqa: B018
