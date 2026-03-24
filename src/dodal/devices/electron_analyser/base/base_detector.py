from typing import Generic

import numpy as np
from ophyd_async.core import (
    Array1D,
    AsyncStatus,
    DetectorArmLogic,
    DetectorTriggerLogic,
    StandardDetector,
    derived_signal_r,
    error_if_none,
)

from dodal.devices.electron_analyser.base.base_driver_io import (
    GenericAnalyserDriverIO,
    TAbstractAnalyserDriverIO,
)
from dodal.devices.electron_analyser.base.base_enums import EnergyMode
from dodal.devices.electron_analyser.base.base_region import (
    GenericRegion,
    TAbstractBaseRegion,
)
from dodal.devices.electron_analyser.base.base_util import to_binding_energy
from dodal.devices.electron_analyser.base.detector_logic import RegionLogic


class ElectronAnalyserDetector(
    StandardDetector,
    Generic[TAbstractAnalyserDriverIO, TAbstractBaseRegion],
):
    """Detector for data acquisition of electron analyser."""

    def __init__(
        self,
        arm_logic: DetectorArmLogic,
        trigger_logic: DetectorTriggerLogic,
        region_logic: RegionLogic,
        # ToDo - Add data logic
        name: str = "",
    ):
        self.add_detector_logics(arm_logic, trigger_logic)
        self._region_logic = region_logic
        self.binding_energy_axis = derived_signal_r(
            self._calculate_binding_energy_axis,
            "eV",
            energy_axis=self._region_logic.driver.energy_axis,
            excitation_energy=self._region_logic.energy_source.energy,
            energy_mode=self._region_logic.driver.energy_mode,
        )
        self.add_config_signals(self.binding_energy_axis)
        super().__init__(name)

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
    async def set(self, region: TAbstractBaseRegion) -> None:
        """Configure detector with regions from plans."""
        await self._region_logic.setup_with_region(region)

    def create_region_detector_list(
        self, regions: list[TAbstractBaseRegion]
    ) -> list["ElectronAnalyserDetector"]:
        """This method can hopefully be dropped when this is merged and released.
        https://github.com/bluesky/bluesky/pull/1978.

        Create a list of detectors equal to the number of regions. Each detector is
        responsible for setting up a specific region.

        Args:
            regions: The list of regions to give to each region detector.

        Returns:
            List of ElectronAnalyserRegionDetector, equal to the number of regions in
            the sequence file.
        """
        arm_logic = error_if_none(self._arm_logic, "arm_logic cannot be None.")
        trigger_logic = error_if_none(
            self._trigger_logic, "trigger_logic cannot be None."
        )
        return [
            ElectronAnalyserDetector(
                arm_logic=arm_logic,
                trigger_logic=trigger_logic,
                region_logic=self._region_logic,
                name=self.name + "_" + r.name,
            )
            for r in regions
        ]


GenericElectronAnalyserDetector = ElectronAnalyserDetector[
    GenericAnalyserDriverIO, GenericRegion
]
