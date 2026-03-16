from ophyd_async.epics.adcore import (
    ADArmLogic,
    ADBaseIO,
    ADWriterType,
    AreaDetector,
)

from dodal.common.beamlines.beamline_utils import get_path_provider
from dodal.common.beamlines.device_helpers import CAM_SUFFIX, TIFF_SUFFIX
from dodal.devices.controllers import ConfigurableImageModeTriggerLogic


def software_triggered_tiff_area_detector(prefix: str, deadtime: float = 0.0):
    """Wrapper for AreaDetector with fixed dead time (defaulted to 0)
    and a TIFF file writer.
    Most detectors in B16 could be configured like this.
    """
    driver = ADBaseIO(prefix + CAM_SUFFIX)
    return AreaDetector(
        prefix=prefix,
        driver=driver,
        arm_logic=ADArmLogic(driver),
        trigger_logic=ConfigurableImageModeTriggerLogic(driver),
        path_provider=get_path_provider(),
        writer_type=ADWriterType.TIFF,
        writer_suffix=TIFF_SUFFIX,
    )
