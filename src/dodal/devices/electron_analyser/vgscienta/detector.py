from collections.abc import Mapping
from typing import Generic

from ophyd_async.core import SignalR

from dodal.devices.electron_analyser.abstract.types import (
    TLensMode,
    TPassEnergyEnum,
    TPsuMode,
)
from dodal.devices.electron_analyser.detector import (
    ElectronAnalyserDetector,
)
from dodal.devices.electron_analyser.enums import SelectedSource
from dodal.devices.electron_analyser.vgscienta.driver_io import (
    VGScientaAnalyserDriverIO,
)
from dodal.devices.electron_analyser.vgscienta.region import (
    VGScientaRegion,
    VGScientaSequence,
)


class VGScientaDetector(
    ElectronAnalyserDetector[
        VGScientaAnalyserDriverIO[TLensMode, TPsuMode, TPassEnergyEnum],
        VGScientaSequence[TLensMode, TPsuMode, TPassEnergyEnum],
        VGScientaRegion[TLensMode, TPassEnergyEnum],
    ],
    Generic[TLensMode, TPsuMode, TPassEnergyEnum],
):
    """
    VGScientaDetector is a specialized detector class for VG Scienta electron analysers.

    This class extends the generic ElectronAnalyserDetector, parameterized for VG Scienta-specific
    driver, sequence, and region types. It provides initialization and configuration for the detector,
    including lens mode, PSU mode, pass energy, and energy sources.

    Args:
        prefix (str): The EPICS PV prefix for the detector.
        lens_mode_type (type[TLensMode]): The type representing lens modes.
        psu_mode_type (type[TPsuMode]): The type representing PSU modes.
        pass_energy_type (type[TPassEnergyEnum]): The type representing pass energy values.
        energy_sources (Mapping[SelectedSource, SignalR[float]]): Mapping of energy sources to their signals.
        name (str, optional): An optional name for the detector. Defaults to "".

    Attributes:
        driver (VGScientaAnalyserDriverIO): The driver instance for the VG Scienta analyser.

    Raises:
        Any exceptions raised by the parent ElectronAnalyserDetector or driver initialization.

    """

    def __init__(
        self,
        prefix: str,
        lens_mode_type: type[TLensMode],
        psu_mode_type: type[TPsuMode],
        pass_energy_type: type[TPassEnergyEnum],
        energy_sources: Mapping[SelectedSource, SignalR[float]],
        name: str = "",
    ):
        driver = VGScientaAnalyserDriverIO[TLensMode, TPsuMode, TPassEnergyEnum](
            prefix, lens_mode_type, psu_mode_type, pass_energy_type, energy_sources
        )
        super().__init__(
            VGScientaSequence[lens_mode_type, psu_mode_type, pass_energy_type],
            driver,
            name,
        )
