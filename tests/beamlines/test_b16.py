from unittest.mock import MagicMock, patch

from dodal.common.beamlines.device_helpers import CAM_SUFFIX, TIFF_SUFFIX
from dodal.devices.b16.detector import software_triggered_tiff_area_detector


def test_software_triggered_tiff_area_detector_calls_with_io_correctly():
    prefix = "PV-PREFIX:"
    default_deadtime = 0.0

    with (
        patch("dodal.devices.b16.detector.ADTIFFWriter.with_io") as mock_writer_with_io,
        patch("dodal.devices.b16.detector.AreaDetector") as mock_area_detector,
        patch(
            "dodal.devices.b16.detector.ConstantDeadTimeController"
        ) as mock_controller,
        patch("dodal.devices.b16.detector.get_path_provider") as mock_get_path_provider,
        patch("dodal.devices.b16.detector.ADBaseIO") as mock_adbase_io,
    ):
        mock_writer = MagicMock(name="Writer")
        mock_writer_with_io.return_value = mock_writer

        mock_path_provider = MagicMock(name="PathProvider")
        mock_get_path_provider.return_value = mock_path_provider

        mock_controller_instance = MagicMock(name="Controller")
        mock_controller.return_value = mock_controller_instance

        mock_driver_instance = MagicMock(name="Driver")
        mock_adbase_io.return_value = mock_driver_instance

        mock_area_detector_instance = MagicMock(name="AreaDetectorInstance")
        mock_area_detector.return_value = mock_area_detector_instance

        result = software_triggered_tiff_area_detector(prefix)  # default deadtime

        # Assert with_io called with correct arguments
        mock_writer_with_io.assert_called_once_with(
            prefix=prefix,
            path_provider=mock_path_provider,
            fileio_suffix=TIFF_SUFFIX,
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
