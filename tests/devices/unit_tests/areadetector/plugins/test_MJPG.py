from pathlib import Path
from unittest.mock import MagicMock, patch

from ophyd.sim import instantiate_fake_device
from PIL import Image

from dodal.devices.areadetector.plugins.MJPG import SnapshotWithBeamCentre
from dodal.devices.oav.oav_detector import OAVConfigParams

DISPLAY_CONFIGURATION = "tests/devices/unit_tests/test_display.configuration"
ZOOM_LEVELS_XML = "tests/devices/unit_tests/test_jCameraManZoomLevels.xml"


@patch("dodal.devices.areadetector.plugins.MJPG.Image")
@patch("dodal.devices.areadetector.plugins.MJPG.os")
@patch("dodal.devices.areadetector.plugins.MJPG.ImageDraw")
@patch("dodal.devices.areadetector.plugins.MJPG.requests")
def test_given_snapshot_triggered_then_crosshair_drawn(
    patch_requests, patch_image_draw, patch_os, patch_image
):
    patch_line = MagicMock()
    patch_requests.get.return_value.content = b""
    params = OAVConfigParams(ZOOM_LEVELS_XML, DISPLAY_CONFIGURATION)
    params.update_on_zoom(1.0, 100, 100)

    patch_image_draw.Draw.return_value.line = patch_line
    snapshot: SnapshotWithBeamCentre = instantiate_fake_device(SnapshotWithBeamCentre)
    snapshot.oav_params = params
    snapshot.directory.set("/tmp/")
    snapshot.filename.set("test")

    status = snapshot.trigger()
    status.wait()

    assert len(patch_line.mock_calls) == 2


def test_snapshot_draws_expected_crosshair(tmp_path: Path):
    image = Image.open("tests/test_data/test_images/oav_snapshot_test.png")
    SnapshotWithBeamCentre.draw_crosshair(image, 510, 380)
    image.save(tmp_path / "output_image.png")
    expected_image = Image.open("tests/test_data/test_images/oav_snapshot_expected.png")
    image_bytes = image.tobytes()
    expected_bytes = expected_image.tobytes()
    assert image_bytes == expected_bytes, "Actual and expected images differ"
