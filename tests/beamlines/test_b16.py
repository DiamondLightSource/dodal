from unittest.mock import ANY, MagicMock, patch

from dodal.beamlines import b16
from dodal.common.beamlines.device_helpers import CAM_SUFFIX, TIFF_SUFFIX


def test_detector_calls_with_io_correctly():
    prefix = "BL16B-EA-FDS-02:"
    default_deadtime = 0.0

    with (
        patch("dodal.beamlines.b16.ADTIFFWriter.with_io") as mock_writer_with_io,
        patch("dodal.beamlines.b16.AreaDetector") as mock_area_detector,
        patch("dodal.beamlines.b16.ConstantDeadTimeController") as mock_controller,
        patch("dodal.beamlines.b16.ADBaseIO") as mock_adbase_io,
    ):
        mock_writer = MagicMock(name="Writer")
        mock_writer_with_io.return_value = mock_writer

        mock_controller_instance = MagicMock(name="Controller")
        mock_controller.return_value = mock_controller_instance

        mock_driver_instance = MagicMock(name="Driver")
        mock_adbase_io.return_value = mock_driver_instance

        mock_area_detector_instance = MagicMock(name="AreaDetectorInstance")
        mock_area_detector.return_value = mock_area_detector_instance

        result = b16.fds2.build(mock=True)

        # Assert with_io called with correct arguments
        mock_writer_with_io.assert_called_once_with(
            prefix, ANY, fileio_suffix=TIFF_SUFFIX
        )

        # Assert ADBaseIO called with correct prefix + suffix
        mock_adbase_io.assert_called_once_with(prefix + CAM_SUFFIX)

        # Assert ConstantDeadTimeController called with driver and deadtime
        mock_controller.assert_called_once_with(
            driver=mock_driver_instance,
            deadtime=default_deadtime,
        )

        # Assert AreaDetector constructed with correct arguments
        mock_area_detector.assert_called_once_with(
            writer=mock_writer,
            controller=mock_controller_instance,
        )

        # The function should return the AreaDetector instance
        assert result is mock_area_detector_instance
