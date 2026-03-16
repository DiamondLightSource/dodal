from typing import Generic, TypeVar

from ophyd_async.core import DetectorTriggerLogic, SignalDict
from ophyd_async.epics.adcore import (
    ADArmLogic,
    ADBaseIO,
    ADWriterType,
    AreaDetector,
    prepare_exposures,
)

from dodal.common.beamlines.beamline_utils import get_path_provider
from dodal.common.beamlines.device_helpers import CAM_SUFFIX, TIFF_SUFFIX

ADBaseIOT = TypeVar("ADBaseIOT", bound=ADBaseIO)


class TiffTriggerLogic(DetectorTriggerLogic, Generic[ADBaseIOT]):
    def __init__(self, driver: ADBaseIOT, deadtime: float):
        self.driver = driver
        self.deadtime = deadtime

    async def prepare_internal(self, num: int, livetime: float, deadtime: float):
        await prepare_exposures(self.driver, num, livetime, deadtime)

    def get_deadtime(self, config_values: SignalDict) -> float:
        return self.deadtime


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
        trigger_logic=TiffTriggerLogic(driver, deadtime),
        path_provider=get_path_provider(),
        writer_type=ADWriterType.TIFF,
        writer_suffix=TIFF_SUFFIX,
    )
