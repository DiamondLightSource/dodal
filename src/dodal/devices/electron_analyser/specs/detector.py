from collections.abc import Mapping
from typing import Generic

from ophyd_async.core import SignalR

from dodal.devices.electron_analyser.abstract.types import TLensMode, TPsuMode
from dodal.devices.electron_analyser.detector import (
    ElectronAnalyserDetector,
)
from dodal.devices.electron_analyser.enums import SelectedSource
from dodal.devices.electron_analyser.specs.driver_io import SpecsAnalyserDriverIO
from dodal.devices.electron_analyser.specs.region import SpecsRegion, SpecsSequence


class SpecsDetector(
    ElectronAnalyserDetector[
        SpecsAnalyserDriverIO[TLensMode, TPsuMode],
        SpecsSequence[TLensMode, TPsuMode],
        SpecsRegion[TLensMode, TPsuMode],
    ],
    Generic[TLensMode, TPsuMode],
):
    """
    A detector class for the Specs electron analyser, parameterized by lens and PSU modes.

    Inherits from:
        ElectronAnalyserDetector

    Type Parameters:
        TLensMode: Type variable for lens mode.
        TPsuMode: Type variable for PSU mode.

    Args:
        prefix (str): The PV prefix for the detector.
        lens_mode_type (type[TLensMode]): The type representing lens modes.
        psu_mode_type (type[TPsuMode]): The type representing PSU modes.
        energy_sources (Mapping[SelectedSource, SignalR[float]]): Mapping of energy sources to their signals.
        name (str, optional): Name of the detector instance. Defaults to "".

    Attributes:
        driver (SpecsAnalyserDriverIO): The driver instance for the detector.

    """

    def __init__(
        self,
        prefix: str,
        lens_mode_type: type[TLensMode],
        psu_mode_type: type[TPsuMode],
        energy_sources: Mapping[SelectedSource, SignalR[float]],
        name: str = "",
    ):
        driver = SpecsAnalyserDriverIO[TLensMode, TPsuMode](
            prefix, lens_mode_type, psu_mode_type, energy_sources
        )
        super().__init__(SpecsSequence[lens_mode_type, psu_mode_type], driver, name)
