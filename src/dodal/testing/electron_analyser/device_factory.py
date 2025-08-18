from typing import Any, get_args, get_origin

from dodal.devices.electron_analyser.abstract import (
    TAbstractAnalyserDriverIO,
)
from dodal.devices.electron_analyser.detector import TElectronAnalyserDetector
from dodal.devices.electron_analyser.vgscienta import (
    VGScientaAnalyserDriverIO,
    VGScientaDetector,
)


async def create_driver(
    driver_class: type[TAbstractAnalyserDriverIO],
    **kwargs: Any,
) -> TAbstractAnalyserDriverIO:
    """
    Helper function that helps to reduce the code to setup an analyser driver. The
    parameters used for the enum types are taken directly from the subscripts of the
    class so the user only needs to provide it in one place.

    Args:
        driver_class: The class for the driver which must include the enums in the
                      subscript, for example MyDriverClass[MyLensMode, ...]
        kwargs: Additional key worded arguments that the driver needs for initalisation.
    """
    parameters = {
        "lens_mode_type": get_args(driver_class)[0],
        "psu_mode_type": get_args(driver_class)[1],
    }
    if get_origin(driver_class) is VGScientaAnalyserDriverIO:
        parameters["pass_energy_type"] = get_args(driver_class)[2]

    return driver_class(**(parameters | kwargs))


async def create_detector(
    detector_class: type[TElectronAnalyserDetector],
    **kwargs: Any,
) -> TElectronAnalyserDetector:
    """
    Helper function that helps to reduce the code to setup an analyser detector. The
    parameters used for the enum types are taken directly from the subscripts of the
    class so the user only needs to provide it in one place.

    Args:
        detector_class: The class for the detector which must include the enums in the
                        subscript, for example MyDetectorClass[MyLensMode, ...]
        kwargs: Additional key worded arguments that the detector needs for
                initalisation.
    """
    parameters = {
        "lens_mode_type": get_args(detector_class)[0],
        "psu_mode_type": get_args(detector_class)[1],
    }
    if get_origin(detector_class) is VGScientaDetector:
        parameters["pass_energy_type"] = get_args(detector_class)[2]

    return detector_class(**(parameters | kwargs))
