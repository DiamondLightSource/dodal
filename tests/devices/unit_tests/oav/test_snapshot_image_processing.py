from pathlib import Path

import pytest
from PIL import Image

from dodal.devices.oav.snapshots.snapshot_image_processing import (
    compute_beam_centre_pixel_xy_for_mm_position,
    draw_crosshair,
)


def test_snapshot_draws_expected_crosshair(tmp_path: Path):
    image = Image.open("tests/test_data/test_images/oav_snapshot_test.png")
    draw_crosshair(image, 510, 380)
    image.save(tmp_path / "output_image.png")
    expected_image = Image.open("tests/test_data/test_images/oav_snapshot_expected.png")
    image_bytes = image.tobytes()
    expected_bytes = expected_image.tobytes()
    assert image_bytes == expected_bytes, "Actual and expected images differ"


@pytest.mark.parametrize(
    "sample_pos_mm, beam_pos_at_origin_px, microns_per_pixel, expected_centre_px",
    [
        [(0.0, 0.0), (100, 200), (1.0, 0.5), (100, 200)],
        [(0.5, 0.1), (100, 200), (1.0, 0.5), (600, 400)],
        [(0.5, 0.1), (20, 40), (1.0, 0.5), (520, 240)],
    ],
)
def test_compute_beam_centre(
    sample_pos_mm: tuple[float, float],
    beam_pos_at_origin_px: tuple[int, int],
    microns_per_pixel: tuple[float, float],
    expected_centre_px: tuple[int, int],
):
    x_px, y_px = compute_beam_centre_pixel_xy_for_mm_position(
        sample_pos_mm, beam_pos_at_origin_px, microns_per_pixel
    )
    assert (x_px, y_px) == expected_centre_px
