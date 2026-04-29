from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from ophyd_async.core import SignalDict
from ophyd_async.epics.adcore import ADWriterType

from dodal.common.beamlines.device_helpers import CAM_SUFFIX, TIFF_SUFFIX
from dodal.devices.beamlines.b16.detector import (
    TiffTriggerLogic,
    software_triggered_tiff_area_detector,
)


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


def test_tiff_trigger_logic_get_deadtime():
    driver = MagicMock()
    logic = TiffTriggerLogic(driver, deadtime=0.123)
    result = logic.get_deadtime(SignalDict())
    assert result == 0.123


@pytest.mark.asyncio
async def test_tiff_trigger_logic_prepare_internal_calls_prepare_exposures():
    driver = MagicMock()
    logic = TiffTriggerLogic(driver, deadtime=0.5)

    with patch(
        "dodal.devices.beamlines.b16.detector.prepare_exposures",
        new_callable=AsyncMock,
    ) as mock_prepare:
        await logic.prepare_internal(num=5, livetime=1.0, deadtime=0.2)

        mock_prepare.assert_awaited_once_with(
            driver,
            5,
            1.0,
            0.2,
        )
