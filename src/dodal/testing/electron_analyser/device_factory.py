from typing import TypeVar, get_args, get_origin

from ophyd_async.core import SignalR, init_devices

from dodal.devices.electron_analyser.abstract import (
    AbstractAnalyserDriverIO,
    AbstractElectronAnalyserDetector,
)
from dodal.devices.electron_analyser.vgscienta import (
    VGScientaAnalyserDriverIO,
    VGScientaDetector,
)

_TDevice = TypeVar(
    "_TDevice", bound=AbstractElectronAnalyserDetector | AbstractAnalyserDriverIO
)


async def create_analyser_device(
    device_class: type[_TDevice],
    energy_sources: dict[str, SignalR[float]],
) -> _TDevice:
    parameters = {
        "prefix": "TEST:",
        "lens_mode_type": get_args(device_class)[0],
        "psu_mode_type": get_args(device_class)[1],
        "energy_sources": energy_sources,
    }
    origin = get_origin(device_class)
    if origin in (VGScientaDetector, VGScientaAnalyserDriverIO):
        parameters["pass_energy_type"] = get_args(device_class)[2]

    is_detector = isinstance(device_class, AbstractElectronAnalyserDetector)
    parameters["name"] = "sim_detector" if is_detector else "sim_driver"

    async with init_devices(mock=True, connect=True):
        device = device_class(**parameters)
    return device
