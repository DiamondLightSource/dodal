from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar, Generic, TypeAlias, TypeVar

import numpy as np
from bluesky.protocols import Movable
from ophyd_async.core import (
    Array1D,
    AsyncStatus,
    SignalR,
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
    SupersetEnum,
    derived_signal_r,
    soft_signal_rw,
)
from ophyd_async.epics.adcore import ADBaseIO
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.devices.electron_analyser.base.base_enums import EnergyMode
from dodal.devices.electron_analyser.base.base_region import (
    AnyAcqMode,
    AnyLensMode,
    AnyPassEnergy,
    GenericRegion,
    TAcquisitionMode,
    TBaseRegion,
    TLensMode,
    TPassEnergy,
)

AnyPsuMode: TypeAlias = SupersetEnum | StrictEnum | str
TPsuMode = TypeVar("TPsuMode", bound=AnyPsuMode)


@dataclass(frozen=True)
class ElectronAnalyserPVConfig:
    """Configuration for PV's. Temporary work around until PV's are standardised between
    beamlines.
    """

    low_energy: str = "LOW_ENERGY"
    high_energy: str = "HIGH_ENERGY"
    centre_energy: str = "CENTRE_ENERGY"
    slices: str = "SLICES"
    lens_mode: str = "LENS_MODE"
    pass_energy: str = "PASS_ENERGY"
    energy_step: str = "STEP_SIZE"
    iterations: str = "NumExposures"
    acquisition_mode: str = "ACQ_MODE"
    psu_mode: str = "PSU_MODE"
    total_steps: str = "TOTAL_POINTS_RBV"


class AbstractAnalyserDriverIO(
    ABC,
    StandardReadable,
    ADBaseIO,
    Movable[TBaseRegion],
    Generic[TBaseRegion, TAcquisitionMode, TLensMode, TPsuMode, TPassEnergy],
):
    """Driver device that defines signals and readables that should be common to all
    electron analysers. Implementations of electron analyser devices should inherit
    from this class and define additional specialised signals and methods.

    Args:
        prefix (str): Base PV to connect to EPICS for this device.
        acquisition_mode_type (type[TAcquisitionMode]): Enum that determines the
            available acquisition modes for this device.
        lens_mode_type (type[TLensMode]): Enum that determines the available lens
            mode for this device.
        psu_mode_type (type[TPsuMode]): Enum that determines the available psu modes
            for this device.
        pass_energy_type (type[TPassEnergy]): Can be enum or float, depending on
            electron analyser model. If enum, it determines the available pass
            energies for this device.
        name (str, optional): Name of the device.
    """

    PV_CFG: ClassVar[ElectronAnalyserPVConfig]

    def __init__(
        self,
        prefix: str,
        acquisition_mode_type: type[TAcquisitionMode],
        lens_mode_type: type[TLensMode],
        psu_mode_type: type[TPsuMode],
        pass_energy_type: type[TPassEnergy],
        name: str = "",
    ) -> None:
        self.acquisition_mode_type = acquisition_mode_type
        self.lens_mode_type = lens_mode_type
        self.psu_mode_type = psu_mode_type
        self.pass_energy_type = pass_energy_type

        # Must call first to initiate parent variables
        super().__init__(prefix=prefix, name=name)

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            # Read once per scan after data acquired
            # Used for setting up region data acquisition
            self.region_name = soft_signal_rw(str, initial_value="null")
            self.energy_mode = soft_signal_rw(
                EnergyMode, initial_value=EnergyMode.KINETIC
            )
            self.low_energy = epics_signal_rw(float, prefix + self.PV_CFG.low_energy)
            self.centre_energy = epics_signal_rw(
                float, prefix + self.PV_CFG.centre_energy
            )
            self.high_energy = epics_signal_rw(float, prefix + self.PV_CFG.high_energy)
            self.slices = epics_signal_rw(int, prefix + self.PV_CFG.slices)
            self.lens_mode = epics_signal_rw(
                lens_mode_type, prefix + self.PV_CFG.lens_mode
            )
            self.pass_energy = epics_signal_rw(
                pass_energy_type, prefix + self.PV_CFG.pass_energy
            )
            self.energy_step = epics_signal_rw(float, prefix + self.PV_CFG.energy_step)
            self.iterations = epics_signal_rw(int, prefix + self.PV_CFG.iterations)
            self.acquisition_mode = epics_signal_rw(
                acquisition_mode_type, prefix + self.PV_CFG.acquisition_mode
            )
            # This is used by each electron analyser, however it is not writeable for
            # all types and it depends on the electron analyser type to know if is moved
            # with region settings.
            self.psu_mode = epics_signal_r(psu_mode_type, prefix + self.PV_CFG.psu_mode)

        # This is defined in the parent class, add it as readable configuration.
        self.add_readables([self.acquire_time], StandardReadableFormat.CONFIG_SIGNAL)

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            # NOT used for setting up region data acquisition.
            self.energy_axis = self._create_energy_axis_signal(prefix)
            self.angle_axis = self._create_angle_axis_signal(prefix)
            self.total_steps = epics_signal_r(int, prefix + self.PV_CFG.total_steps)
            self.total_time = derived_signal_r(
                self._calculate_total_time,
                "s",
                total_steps=self.total_steps,
                step_time=self.acquire_time,
                iterations=self.iterations,
            )

    @abstractmethod
    @AsyncStatus.wrap
    async def set(self, epics_region: TBaseRegion):
        """Move a group of signals defined in a region. Each implementation of this
        class is responsible for implementing this method correctly.

        Args:
            epics_region (TBaseRegion): Contains the parameters to setup the
                driver for a scan.
        """

    @abstractmethod
    def _create_angle_axis_signal(self, prefix: str) -> SignalR[Array1D[np.float64]]:
        """The signal that defines the angle axis. Depends on analyser model.

        Args:
            prefix (str): PV string used for connecting to angle axis.

        Returns:
            SignalR that can give us angle axis array data.
        """

    @abstractmethod
    def _create_energy_axis_signal(self, prefix: str) -> SignalR[Array1D[np.float64]]:
        """The signal that defines the energy axis. Depends on analyser model.

        Args:
            prefix (str): PV string used for connecting to energy axis.

        Returns:
            Signal that can give us energy axis array data.
        """

    def _calculate_total_time(
        self, total_steps: int, step_time: float, iterations: int
    ) -> float:
        """Calulcate the total time the scan takes for this region. Function for a
        derived signal.

        Args:
            total_steps (int): Number of steps for the region.
            step_time (float): Time for each step for the region.
            iterations (int): The number of iterations the region collected data for.

        Returns:
            Float: Calculated total time in seconds.
        """
        return total_steps * step_time * iterations


GenericAnalyserDriverIO = AbstractAnalyserDriverIO[
    GenericRegion, AnyAcqMode, AnyLensMode, AnyPsuMode, AnyPassEnergy
]
TAbstractAnalyserDriverIO = TypeVar(
    "TAbstractAnalyserDriverIO", bound=AbstractAnalyserDriverIO
)
