from ophyd_async.epics.adcore import (
    ADBaseIO,
    ADTIFFWriter,
    AreaDetector,
)

from dodal.common.beamlines.beamline_utils import get_path_provider
from dodal.common.beamlines.device_helpers import CAM_SUFFIX, TIFF_SUFFIX
from dodal.devices.controllers import ConstantDeadTimeController


def software_triggered_tiff_area_detector(prefix: str, deadtime: float = 0.0):
    """
    Wrapper for AreaDetector with fixed dead time (defaulted to 0)
    and a TIFF file writer.
    Most detectors in B16 could be configured like this
    """
    return AreaDetector(
        writer=ADTIFFWriter.with_io(
            prefix=prefix, path_provider=get_path_provider(), fileio_suffix=TIFF_SUFFIX
        ),
        controller=ConstantDeadTimeController(
            driver=ADBaseIO(prefix + CAM_SUFFIX), deadtime=deadtime
        ),
    )
