from pathlib import Path

import numpy as np
import pytest
from daq_config_server.client import ConfigClient

from dodal.devices.beamlines.i10.rasor.halbach import HalbachLookupTable
from tests.devices.beamlines.i10.test_data import HALBACH_LUT_CSV


@pytest.fixture
def simple_lut() -> HalbachLookupTable:
    """2x2 lookup table for unit tests."""
    h_grid = np.array([0.0, 10.0])
    angle_grid = np.array([0.0, 20.0])
    motor_grid = np.array(
        [
            [[0.0, 0.0, 0.0, 0.0], [10.0, 20.0, 30.0, 40.0]],
            [[100.0, 200.0, 300.0, 400.0], [110.0, 220.0, 330.0, 440.0]],
        ]
    )
    return HalbachLookupTable(
        h_grid=h_grid,
        angle_grid=angle_grid,
        motor_grid=motor_grid,
    )


def test_invalid_motor_grid_shape() -> None:
    with pytest.raises(ValueError, match="Expected motor_grid shape"):
        HalbachLookupTable(
            h_grid=np.array([0.0, 10.0]),
            angle_grid=np.array([0.0, 20.0]),
            motor_grid=np.zeros((2, 3, 4)),
        )


def test_h_limits_returns_min_and_max(simple_lut: HalbachLookupTable) -> None:
    assert simple_lut.h_limits == (0.0, 10.0)


def test_angle_limits_returns_min_and_max(simple_lut: HalbachLookupTable) -> None:
    assert simple_lut.angle_limits == (0.0, 20.0)


@pytest.mark.parametrize(
    ("val", "expected_idx", "expected_weight"),
    [
        (-10.0, 0, 0.0),
        (10.0, 1, 1.0),
        (2.5, 1, 0.25),
    ],
)
def test_index_and_weight(
    val: float,
    expected_idx: int,
    expected_weight: float,
) -> None:
    grid = np.array([-10.0, 0.0, 10.0])
    idx, weight = HalbachLookupTable._index_and_weight(grid, val)
    assert idx == expected_idx
    assert weight == pytest.approx(expected_weight)


@pytest.mark.parametrize(
    ("h_mt", "field_angle_z_deg", "expected_motors"),
    [
        (10.0, 20.0, [110.0, 220.0, 330.0, 440.0]),
        (5.0, 0.0, [50.0, 100.0, 150.0, 200.0]),
        (0.0, 5.0, [2.5, 5.0, 7.5, 10.0]),
        (2.5, 10.0, [30.0, 60.0, 90.0, 120.0]),
    ],
)
def test_interpolate(
    simple_lut: HalbachLookupTable,
    h_mt: float,
    field_angle_z_deg: float,
    expected_motors: list[float],
) -> None:
    result = simple_lut.interpolate(h_mt=h_mt, field_angle_z_deg=field_angle_z_deg)
    assert result == pytest.approx(expected_motors)


@pytest.mark.parametrize(
    ("h_mt", "field_angle_z_deg"),
    [
        (-0.1, 5.0),
        (10.1, 5.0),
        (5.0, -0.1),
        (5.0, 20.1),
    ],
)
def test_interpolate_out_of_bounds(
    simple_lut: HalbachLookupTable,
    h_mt: float,
    field_angle_z_deg: float,
) -> None:
    with pytest.raises(ValueError, match="outside calibrated LUT bounds"):
        simple_lut.interpolate(h_mt=h_mt, field_angle_z_deg=field_angle_z_deg)


def test_from_csv_sorts_unorganised_rows(tmp_path: Path) -> None:
    csv_file = tmp_path / "unsorted_lut.csv"
    csv_file.write_text(
        "H_mT,Field_Angle_Z_deg,m1_unwrapped_deg,m2_unwrapped_deg,m3_unwrapped_deg,m4_unwrapped_deg\n"
        "10.0,20.0,110.0,220.0,330.0,440.0\n"
        "0.0,20.0,10.0,20.0,30.0,40.0\n"
        "10.0,0.0,100.0,200.0,300.0,400.0\n"
        "0.0,0.0,0.0,0.0,0.0,0.0\n"
    )
    lut = HalbachLookupTable.from_csv(csv_file)
    assert lut.h_grid == pytest.approx([0.0, 10.0])
    assert lut.angle_grid == pytest.approx([0.0, 20.0])
    assert lut.motor_grid[0, 1] == pytest.approx([10.0, 20.0, 30.0, 40.0])
    assert lut.motor_grid[1, 0] == pytest.approx([100.0, 200.0, 300.0, 400.0])


def test_from_csv_on_incomplete_grid(tmp_path: Path) -> None:
    csv_file = tmp_path / "incomplete_lut.csv"
    csv_file.write_text(
        "H_mT,Field_Angle_Z_deg,m1_unwrapped_deg,m2_unwrapped_deg,m3_unwrapped_deg,m4_unwrapped_deg\n"
        "0.0,0.0,0.0,0.0,0.0,0.0\n"
        "0.0,20.0,10.0,20.0,30.0,40.0\n"
        "10.0,0.0,100.0,200.0,300.0,400.0\n"
    )
    with pytest.raises(ValueError, match="does not form a complete regular 2D grid"):
        HalbachLookupTable.from_csv(csv_file)


def test_from_csv_loads_test_lut_file() -> None:
    lut = HalbachLookupTable.from_csv(HALBACH_LUT_CSV)
    assert lut.h_limits == (-170.0, 170.0)
    assert lut.angle_limits == (-110.0, 110.0)
    assert lut.motor_grid.shape == (69, 45, 4)


def test_from_config_server_parses_lut(mock_config_client: ConfigClient) -> None:
    lut = HalbachLookupTable.from_config_server(mock_config_client, HALBACH_LUT_CSV)

    assert lut.h_limits == (-170.0, 170.0)
    assert lut.angle_limits == (-110.0, 110.0)
    assert lut.motor_grid.shape == (69, 45, 4)
