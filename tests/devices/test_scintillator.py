from contextlib import nullcontext
from unittest.mock import AsyncMock, MagicMock, call

import pytest
from ophyd_async.core import Reference, get_mock_put, init_devices, set_mock_value
from ophyd_async.testing import assert_value

from dodal.common.beamlines.beamline_parameters import GDABeamlineParameters
from dodal.devices.aperturescatterguard import (
    ApertureScatterguard,
    ApertureValue,
)
from dodal.devices.mx_phase1.beamstop import Beamstop, BeamstopPositions
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
            "in_beam_x_STANDARD": 1.21,
            "in_beam_y_STANDARD": 45.4,
            "in_beam_z_STANDARD": 30.0,
            "bs_x_tolerance": 0.02,
            "bs_y_tolerance": 0.005,
            "bs_z_tolerance": 0.3,
        }
    )


@pytest.fixture
def beamstop(mock_beamline_parameters) -> Beamstop:
    beamstop = Beamstop("-MO-BS-01:", mock_beamline_parameters, name="beamstop")
    beamstop.selected_pos.get_value = AsyncMock(
        return_value=BeamstopPositions.DATA_COLLECTION
    )
    return beamstop


@pytest.fixture
async def scintillator_and_ap_sg(
    mock_beamline_parameters: GDABeamlineParameters,
    beamstop: Beamstop,
    ap_sg: ApertureScatterguard,
) -> tuple[Scintillator, MagicMock]:
    async with init_devices(mock=True):
        ap_sg.selected_aperture.set = AsyncMock()
        ap_sg.selected_aperture.get_value = AsyncMock()
        ap_sg.get_scin_move_position = MagicMock()
        scintillator = Scintillator(
            prefix="",
            name="test_scin",
            aperture_scatterguard=Reference(ap_sg),
            beamstop=Reference(beamstop),
            beamline_parameters=mock_beamline_parameters,
        )
    set_mock_value(ap_sg.aperture.x.user_readback, 1.0)
    set_mock_value(ap_sg.scatterguard.x.user_readback, 2.0)
    await scintillator.y_mm.set(5)
    await scintillator.z_mm.set(5)
    return scintillator, ap_sg


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
    await scintillator.y_mm.set(100.855)
    await scintillator.z_mm.set(101.5115)
    with pytest.raises(ValueError):
        await scintillator.selected_pos.set(InOut.UNKNOWN)


async def test_given_aperture_scatterguard_parked_when_set_to_out_position_then_returns_expected(
    scintillator_and_ap_sg: tuple[Scintillator, ApertureScatterguard],
):
    scintillator, ap_sg = scintillator_and_ap_sg
    ap_sg.selected_aperture.get_value.return_value = ApertureValue.PARKED  # type: ignore

    await scintillator.selected_pos.set(InOut.OUT)

    await assert_value(scintillator.y_mm.user_setpoint, -0.02)
    await assert_value(scintillator.z_mm.user_setpoint, 0.1)


async def test_given_aperture_scatterguard_parked_when_set_to_in_position_then_returns_expected(
    scintillator_and_ap_sg: tuple[Scintillator, ApertureScatterguard],
):
    scintillator, ap_sg = scintillator_and_ap_sg
    ap_sg.selected_aperture.get_value.return_value = ApertureValue.PARKED  # type: ignore

    await scintillator.selected_pos.set(InOut.IN)

    await assert_value(scintillator.y_mm.user_setpoint, 100.855)
    await assert_value(scintillator.z_mm.user_setpoint, 101.5115)


@pytest.mark.parametrize(
    "y, z, expected_position",
    [
        (100.855, 101.5115, InOut.IN),
        (-0.02, 0.1, InOut.OUT),
    ],
)
async def test_given_scintillator_already_out_when_moved_in_or_out_then_does_nothing(
    scintillator_and_ap_sg: tuple[Scintillator, ApertureScatterguard],
    beamstop: Beamstop,
    expected_position,
    y,
    z,
):
    scintillator, ap_sg = scintillator_and_ap_sg
    ap_sg.get_scin_move_position.return_value = {
        ap_sg.aperture.x: -1.0,
        ap_sg.scatterguard.x: -1.5,
    }
    beamstop.selected_pos.get_value.return_value = BeamstopPositions.UNKNOWN
    await scintillator.y_mm.set(y)
    await scintillator.z_mm.set(z)

    get_mock_put(scintillator.y_mm.user_setpoint).reset_mock()
    get_mock_put(scintillator.z_mm.user_setpoint).reset_mock()

    ap_sg.selected_aperture.get_value.return_value = ApertureValue.LARGE  # type: ignore
    await scintillator.selected_pos.set(expected_position)

    get_mock_put(scintillator.y_mm.user_setpoint).assert_not_called()
    get_mock_put(scintillator.z_mm.user_setpoint).assert_not_called()
    get_mock_put(ap_sg.aperture.x.user_setpoint).assert_not_called()
    get_mock_put(ap_sg.scatterguard.x.user_setpoint).assert_not_called()


@pytest.mark.parametrize(
    "beamstop_position, expected_good",
    [
        [BeamstopPositions.DATA_COLLECTION, True],
        [BeamstopPositions.OUT_OF_BEAM, True],
        [BeamstopPositions.UNKNOWN, False],
    ],
)
async def test_beamstop_check_in_known_good_position(
    scintillator_and_ap_sg: tuple[Scintillator, ApertureScatterguard],
    beamstop: Beamstop,
    beamstop_position: BeamstopPositions,
    expected_good: bool,
):
    beamstop.selected_pos.get_value.return_value = beamstop_position
    scintillator, _ = scintillator_and_ap_sg

    with (
        pytest.raises(
            ValueError, match="Scintillator cannot be moved due to beamstop position"
        )
        if not expected_good
        else nullcontext()
    ):
        await scintillator.selected_pos.set(InOut.OUT)


@pytest.mark.parametrize(
    "initial_y, initial_z, final_y, final_z, swap_order, final_position",
    [
        [100.855, 101.5115, -0.02, 0.1, False, InOut.OUT],
        [-0.02, 0.1, 100.855, 101.5115, True, InOut.IN],
    ],
)
async def test_move_scintillator_moves_ap_sg_to_scin_move_and_back(
    scintillator_and_ap_sg: tuple[Scintillator, ApertureScatterguard],
    initial_y: float,
    initial_z: float,
    final_y: float,
    final_z: float,
    swap_order: bool,
    final_position: InOut,
):
    scintillator, ap_sg = scintillator_and_ap_sg
    ap_sg.get_scin_move_position.return_value = {
        ap_sg.aperture.x: -1.0,
        ap_sg.scatterguard.x: -1.5,
    }
    set_mock_value(scintillator.y_mm.user_readback, initial_y)
    set_mock_value(scintillator.z_mm.user_readback, initial_z)

    parent = MagicMock()
    parent.aperture.attach_mock(get_mock_put(ap_sg.aperture.x.user_setpoint), "x")
    parent.aperture.attach_mock(get_mock_put(ap_sg.aperture.y.user_setpoint), "y")
    parent.aperture.attach_mock(get_mock_put(ap_sg.aperture.z.user_setpoint), "z")
    parent.scatterguard.attach_mock(
        get_mock_put(ap_sg.scatterguard.x.user_setpoint), "x"
    )
    parent.scatterguard.attach_mock(
        get_mock_put(ap_sg.scatterguard.y.user_setpoint), "y"
    )
    parent.scintillator.attach_mock(
        get_mock_put(scintillator.y_mm.user_setpoint), "y_mm"
    )
    parent.scintillator.attach_mock(
        get_mock_put(scintillator.z_mm.user_setpoint), "z_mm"
    )
    await scintillator.selected_pos.set(final_position)

    expected_scintillator_move = [
        call.scintillator.y_mm(final_y, wait=True),
        call.scintillator.z_mm(final_z, wait=True),
    ]
    if swap_order:
        expected_scintillator_move = expected_scintillator_move[::-1]
    expected_calls = (
        [call.aperture.x(-1.0, wait=True), call.scatterguard.x(-1.5, wait=True)]
        + expected_scintillator_move
        + [
            call.aperture.x(1.0, wait=True),
            call.scatterguard.x(2.0, wait=True),
        ]
    )
    parent.assert_has_calls(expected_calls)
