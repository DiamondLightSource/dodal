from unittest.mock import MagicMock, patch

from ophyd_async.epics.adcore import ADWriterType

from dodal.common.beamlines.device_helpers import CAM_SUFFIX, TIFF_SUFFIX
from dodal.devices.beamlines.b16.detector import software_triggered_tiff_area_detector


def test_software_triggered_tiff_area_detector_calls_with_io_correctly():
    prefix = "PV-PREFIX:"
    default_deadtime = 0.0

    with (
        patch(
            "dodal.devices.beamlines.b16.detector.AreaDetector"
        ) as mock_area_detector,
        patch(
            "dodal.devices.beamlines.b16.detector.TiffTriggerLogic"
        ) as mock_tiff_trigger_logic,
        patch(
            "dodal.devices.beamlines.b16.detector.get_path_provider"
        ) as mock_get_path_provider,
        patch("dodal.devices.beamlines.b16.detector.ADBaseIO") as mock_adbase_io,
        patch("dodal.devices.beamlines.b16.detector.ADArmLogic") as mock_arm_logic,
    ):
        mock_arm_logic_instance = MagicMock(name="ADArmLogic")
        mock_arm_logic.return_value = mock_arm_logic_instance

        mock_path_provider = MagicMock(name="PathProvider")
        mock_get_path_provider.return_value = mock_path_provider

        mock_tiff_trigger_logic_instance = MagicMock(name="TriggerLogic")
        mock_tiff_trigger_logic.return_value = mock_tiff_trigger_logic_instance

        mock_driver_instance = MagicMock(name="Driver")
        mock_adbase_io.return_value = mock_driver_instance

        mock_area_detector_instance = MagicMock(name="AreaDetectorInstance")
        mock_area_detector.return_value = mock_area_detector_instance

        result = software_triggered_tiff_area_detector(prefix)  # default deadtime

        # Assert ADBaseIO called with correct prefix + suffix
        mock_adbase_io.assert_called_once_with(prefix + CAM_SUFFIX)

        # Assert correct TriggerLogic used.
        mock_arm_logic.assert_called_once_with(mock_driver_instance)

        # Assert TiffTriggerLogic called with driver and deadtime
        mock_tiff_trigger_logic.assert_called_once_with(
            mock_driver_instance,
            default_deadtime,
        )

        # Assert AreaDetector constructed with correct arguments
        mock_area_detector.assert_called_once_with(
            prefix=prefix,
            driver=mock_driver_instance,
            # writer=mock_writer,
            trigger_logic=mock_tiff_trigger_logic_instance,
            path_provider=mock_path_provider,
            arm_logic=mock_arm_logic_instance,
            writer_type=ADWriterType.TIFF,
            writer_suffix=TIFF_SUFFIX,
        )

        # The function should return the AreaDetector instance
        assert result is mock_area_detector_instance
