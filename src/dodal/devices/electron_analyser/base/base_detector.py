import asyncio
from collections.abc import Mapping, Sequence
from typing import Generic

import numpy as np
from bluesky.protocols import Preparable, Stageable
from ophyd_async.core import (
    Array1D,
    AsyncStatus,
    DetectorAcquireLogic,
    SignalR,
    derived_signal_r,
)
from ophyd_async.epics.adcore import ADWriterFactory, AreaDetector, NDPluginBaseIO

from dodal.devices.electron_analyser.base.base_driver_io import (
    GenericAnalyserDriverIO,
    TAbstractAnalyserDriverIO,
)
from dodal.devices.electron_analyser.base.base_enums import EnergyMode
from dodal.devices.electron_analyser.base.base_region import (
    BaseRegion,
    BaseSequence,
    GenericRegion,
    TBaseRegion,
)
from dodal.devices.electron_analyser.base.base_util import to_binding_energy
from dodal.devices.electron_analyser.base.detector_logic import (
    ElectronAnalayserTriggerLogic,
    RegionLogic,
)


class SequenceHolder(Stageable, Preparable):
    """Wrapper to hold the sequence data for an electron analyser.

    Used in scans when we need to hold the state of the configured sequence of regions
    to give to the electron analyser for each step of a scan.
    """

    def __init__(self):
        self.data: BaseSequence[BaseRegion] | None = None

    @AsyncStatus.wrap
    async def prepare(self, value: BaseSequence[BaseRegion] | None):
        self.data = value

    @AsyncStatus.wrap
    async def stage(self):
        pass

    @AsyncStatus.wrap
    async def unstage(self):
        self.data = None


class ElectronAnalyserDetector(
    AreaDetector[TAbstractAnalyserDriverIO],
    Generic[TAbstractAnalyserDriverIO, TBaseRegion],
):
    """Detector for data acquisition of electron analyser. Can be configured with
    region data via set method.
    """

    def __init__(
        self,
        driver: TAbstractAnalyserDriverIO,
        prefix: str,
        *writer_factories: ADWriterFactory,
        acquire_logic: DetectorAcquireLogic,
        trigger_logic: ElectronAnalayserTriggerLogic[TAbstractAnalyserDriverIO],
        region_logic: RegionLogic,
        plugins: Mapping[str, NDPluginBaseIO] | None = None,
        config_sigs: Sequence[SignalR] = (),
        name: str = "",
    ):
        self.sequence = SequenceHolder()
        self._region_logic = region_logic
        self.binding_energy_axis = derived_signal_r(
            self._calculate_binding_energy_axis,
            "eV",
            energy_axis=region_logic.driver.energy_axis,
            excitation_energy=region_logic.energy_source,
            energy_mode=region_logic.driver.energy_mode,
        )
        config_sigs = (self.binding_energy_axis, *config_sigs)
        super().__init__(
            driver,
            prefix,
            *writer_factories,
            acquire_logic=acquire_logic,
            trigger_logic=trigger_logic,
            plugins=plugins,
            config_sigs=config_sigs,
            name=name,
        )

    def _calculate_binding_energy_axis(
        self,
        energy_axis: Array1D[np.float64],
        excitation_energy: float,
        energy_mode: EnergyMode,
    ) -> Array1D[np.float64]:
        """Calculate the binding energy axis to calibrate the spectra data. Function for
        a derived signal.

        Args:
            energy_axis (Array1D[np.float64]): Array data of the original energy_axis
                from epics.
            excitation_energy (float): The excitation energy value used for the scan of
                this region.
            energy_mode (EnergyMode): The energy_mode of the region that was used for
                the scan of this region.

        Returns:
            Array that is the correct axis for the spectra data.
        """
        is_binding = energy_mode == EnergyMode.BINDING
        return np.array(
            [
                to_binding_energy(i_energy_axis, EnergyMode.KINETIC, excitation_energy)
                if is_binding
                else i_energy_axis
                for i_energy_axis in energy_axis
            ]
        )

    @AsyncStatus.wrap
    async def set(self, region: TBaseRegion) -> None:
        """Configure detector with regions from plans."""
        await self._region_logic.setup_with_region(region)

    @AsyncStatus.wrap
    async def stage(self) -> None:
        """Prepare the detector for use by ensuring it is idle and ready.

        This method asynchronously stages the detector by disarming the controller to
        ensure the detector is not actively acquiring data.

        Raises:
            Any exceptions raised by the driver's stage or controller's disarm methods.
        """
        await asyncio.gather(super().stage(), self.sequence.stage())

    @AsyncStatus.wrap
    async def unstage(self) -> None:
        """Disarm the detector."""
        await asyncio.gather(super().unstage(), self.sequence.unstage())


GenericElectronAnalyserDetector = ElectronAnalyserDetector[
    GenericAnalyserDriverIO, GenericRegion
]
