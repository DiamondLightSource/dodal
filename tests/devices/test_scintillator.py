from unittest.mock import AsyncMock, MagicMock

import pytest
from ophyd_async.core import get_mock_put, init_devices
from ophyd_async.testing import assert_value

from dodal.common.beamlines.beamline_parameters import GDABeamlineParameters
from dodal.devices.aperturescatterguard import ApertureScatterguard, ApertureValue
from dodal.devices.scintillator import InOut, Scintillator


@pytest.fixture
def mock_beamline_parameters() -> GDABeamlineParameters:
    return GDABeamlineParameters(
        params={
            "scin_y_SCIN_IN": 100.855,
            "scin_y_SCIN_OUT": -0.02,
            "scin_z_SCIN_IN": 101.5115,
            "scin_z_SCIN_OUT": 0.1,
            "scin_y_tolerance": 0.1,
            "scin_z_tolerance": 0.12,
        }
    )


@pytest.fixture
async def scintillator_and_ap_sg(
    mock_beamline_parameters: GDABeamlineParameters,
) -> tuple[Scintillator, MagicMock]:
    async with init_devices(mock=True):
        mock_ap_sg = MagicMock()
        mock_ap_sg.return_value.selected_aperture.set = AsyncMock()
        mock_ap_sg.return_value.selected_aperture.get_value = AsyncMock()
        scintillator = Scintillator(
            prefix="",
            name="test_scin",
            aperture_scatterguard=mock_ap_sg,
            beamline_parameters=mock_beamline_parameters,
        )
    await scintillator.y_mm.set(5)
    await scintillator.z_mm.set(5)
    return scintillator, mock_ap_sg


@pytest.mark.parametrize(
    "y, z, expected_position",
    [
        (100.855, 101.5115, InOut.IN),
        (-0.02, 0.1, InOut.OUT),
        (0.1, 0.1, InOut.UNKNOWN),
        (10.2, 15.6, InOut.UNKNOWN),
    ],
)
async def test_given_at_positions_when_position_read_then_returns_expected(
    scintillator_and_ap_sg: tuple[Scintillator, ApertureScatterguard],
    y: float,
    z: float,
    expected_position: InOut,
):
    scintillator, _ = scintillator_and_ap_sg
    await scintillator.y_mm.set(y)
    await scintillator.z_mm.set(z)

    in_out = await scintillator.selected_pos.get_value()
    assert in_out == expected_position


async def test_when_set_to_unknown_position_then_error_raised(
    scintillator_and_ap_sg: tuple[Scintillator, ApertureScatterguard],
):
    scintillator, _ = scintillator_and_ap_sg
    with pytest.raises(ValueError):
        await scintillator.selected_pos.set(InOut.UNKNOWN)


async def test_given_aperture_scatterguard_parked_when_set_to_out_position_then_returns_expected(
    scintillator_and_ap_sg: tuple[Scintillator, ApertureScatterguard],
):
    scintillator, ap_sg = scintillator_and_ap_sg
    ap_sg.return_value.selected_aperture.get_value.return_value = ApertureValue.PARKED  # type: ignore

    await scintillator.selected_pos.set(InOut.OUT)

    await assert_value(scintillator.y_mm.user_setpoint, -0.02)
    await assert_value(scintillator.z_mm.user_setpoint, 0.1)


async def test_given_aperture_scatterguard_parked_when_set_to_in_position_then_returns_expected(
    scintillator_and_ap_sg: tuple[Scintillator, ApertureScatterguard],
):
    scintillator, ap_sg = scintillator_and_ap_sg
    ap_sg.return_value.selected_aperture.get_value.return_value = ApertureValue.PARKED  # type: ignore

    await scintillator.selected_pos.set(InOut.IN)

    await assert_value(scintillator.y_mm.user_setpoint, 100.855)
    await assert_value(scintillator.z_mm.user_setpoint, 101.5115)


@pytest.mark.parametrize("scint_pos", [InOut.OUT, InOut.IN])
async def test_given_aperture_scatterguard_not_parked_when_set_to_in_or_out_position_then_exception_raised(
    scintillator_and_ap_sg: tuple[Scintillator, ApertureScatterguard], scint_pos
):
    for position in ApertureValue:
        if position != ApertureValue.PARKED:
            scintillator, ap_sg = scintillator_and_ap_sg
            ap_sg.return_value.selected_aperture.get_value.return_value = position  # type: ignore
            with pytest.raises(ValueError):
                await scintillator.selected_pos.set(scint_pos)


@pytest.mark.parametrize(
    "y, z, expected_position",
    [
        (100.855, 101.5115, InOut.IN),
        (-0.02, 0.1, InOut.OUT),
    ],
)
async def test_given_scintillator_already_out_when_moved_in_or_out_then_does_nothing(
    scintillator_and_ap_sg: tuple[Scintillator, ApertureScatterguard],
    expected_position,
    y,
    z,
):
    scintillator, ap_sg = scintillator_and_ap_sg
    await scintillator.y_mm.set(y)
    await scintillator.z_mm.set(z)

    get_mock_put(scintillator.y_mm.user_setpoint).reset_mock()
    get_mock_put(scintillator.z_mm.user_setpoint).reset_mock()

    ap_sg.return_value.selected_aperture.get_value.return_value = ApertureValue.LARGE  # type: ignore
    await scintillator.selected_pos.set(expected_position)

    get_mock_put(scintillator.y_mm.user_setpoint).assert_not_called()
    get_mock_put(scintillator.z_mm.user_setpoint).assert_not_called()
