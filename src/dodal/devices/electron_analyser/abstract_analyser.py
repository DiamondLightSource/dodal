import asyncio
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

import numpy as np
from bluesky.protocols import (
    Reading,
    Stageable,
    Triggerable,
)
from event_model import DataKey
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    Array1D,
    AsyncStatus,
    Device,
    SignalR,
    StandardReadable,
    StandardReadableFormat,
    derived_signal_r,
    set_and_wait_for_value,
    soft_signal_rw,
)
from ophyd_async.core._protocol import AsyncConfigurable, AsyncReadable
from ophyd_async.core._utils import merge_gathered_dicts  # type: ignore
from ophyd_async.epics.adcore import (
    DEFAULT_GOOD_STATES,
    ADBaseIO,
    ADState,
    stop_busy_record,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.devices.electron_analyser.abstract_region import EnergyMode
from dodal.devices.electron_analyser.util import to_binding_energy


class AbstractAnalyserDriverIO(ABC, StandardReadable, ADBaseIO):
    """
    Generic device to configure electron analyser with new region settings.
    Electron analysers should inherit from this class for further specialisation.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.image = epics_signal_r(Array1D[np.float64], prefix + "IMAGE")
            self.spectrum = epics_signal_r(Array1D[np.float64], prefix + "INT_SPECTRUM")
            self.total_intensity = derived_signal_r(
                self._calculate_total_intensity, spectrum=self.spectrum
            )
            self.excitation_energy = soft_signal_rw(float, initial_value=0, units="eV")

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            # Used for setting up region data acquisition.
            self.region_name = soft_signal_rw(str, initial_value="null")
            self.energy_mode = soft_signal_rw(
                EnergyMode, initial_value=EnergyMode.KINETIC
            )
            self.low_energy = epics_signal_rw(float, prefix + "LOW_ENERGY")
            self.high_energy = epics_signal_rw(float, prefix + "HIGH_ENERGY")
            self.slices = epics_signal_rw(int, prefix + "SLICES")
            self.lens_mode = epics_signal_rw(str, prefix + "LENS_MODE")
            self.pass_energy = epics_signal_rw(
                self.pass_energy_type, prefix + "PASS_ENERGY"
            )
            self.energy_step = epics_signal_rw(float, prefix + "STEP_SIZE")
            self.iterations = epics_signal_rw(int, prefix + "NumExposures")
            self.acquisition_mode = epics_signal_rw(str, prefix + "ACQ_MODE")

            # Read once per scan after data acquired
            self.energy_axis = self._get_energy_axis_signal(prefix)
            self.binding_energy_axis = derived_signal_r(
                self._calculate_binding_energy_axis,
                "eV",
                energy_axis=self.energy_axis,
                excitation_energy=self.excitation_energy,
                energy_mode=self.energy_mode,
            )
            self.angle_axis = self._get_angle_axis_signal(prefix)
            self.step_time = epics_signal_r(float, prefix + "AcquireTime")
            self.total_steps = epics_signal_r(int, prefix + "TOTAL_POINTS_RBV")
            self.total_time = derived_signal_r(
                self._calculate_total_time,
                "s",
                total_steps=self.total_steps,
                step_time=self.step_time,
                iterations=self.iterations,
            )

        super().__init__(prefix=prefix, name=name)

    @abstractmethod
    def _get_angle_axis_signal(self, prefix: str = "") -> SignalR:
        """
        The signal that defines the angle axis. Depends on analyser model.
        """

    @abstractmethod
    def _get_energy_axis_signal(self, prefix: str = "") -> SignalR:
        """
        The signal that defines the energy axis. Depends on analyser model.
        """

    def _calculate_binding_energy_axis(
        self,
        energy_axis: Array1D[np.float64],
        excitation_energy: float,
        energy_mode: EnergyMode,
    ) -> Array1D[np.float64]:
        is_binding = energy_mode == EnergyMode.BINDING
        return np.array(
            [
                to_binding_energy(i_energy_axis, EnergyMode.KINETIC, excitation_energy)
                if is_binding
                else i_energy_axis
                for i_energy_axis in energy_axis
            ]
        )

    def _calculate_total_time(
        self, total_steps: int, step_time: float, iterations: int
    ) -> float:
        return total_steps * step_time * iterations

    def _calculate_total_intensity(self, spectrum: Array1D[np.float64]) -> float:
        return np.sum(spectrum)

    @property
    @abstractmethod
    def pass_energy_type(self) -> type:
        """
        Return the type the pass_energy should be. Each one is unfortunately different
        for the underlying analyser software and cannot be changed on epics side.
        """


TAbstractAnalyserDriverIO = TypeVar(
    "TAbstractAnalyserDriverIO", bound=AbstractAnalyserDriverIO
)


class AnalyserController(Generic[TAbstractAnalyserDriverIO]):
    def __init__(
        self,
        driver: TAbstractAnalyserDriverIO,
        good_states: frozenset[ADState] = DEFAULT_GOOD_STATES,
    ) -> None:
        self.driver = driver
        self.good_states = good_states
        self.frame_timeout = DEFAULT_TIMEOUT
        self._arm_status: AsyncStatus | None = None

    async def arm(self):
        self._arm_status = await self.start_acquiring_driver_and_ensure_status()

    async def disarm(self):
        # We can't use caput callback as we already used it in arm() and we can't have
        # 2 or they will deadlock
        await stop_busy_record(self.driver.acquire, False, timeout=1)

    async def start_acquiring_driver_and_ensure_status(self) -> AsyncStatus:
        """Start acquiring driver, raising ValueError if the detector is in a bad state.
        This sets driver.acquire to True, and waits for it to be True up to a timeout.
        Then, it checks that the DetectorState PV is in DEFAULT_GOOD_STATES,
        and otherwise raises a ValueError.
        :returns AsyncStatus:
            An AsyncStatus that can be awaited to set driver.acquire to True and perform
            subsequent raising (if applicable) due to detector state.
        """
        status = await set_and_wait_for_value(
            self.driver.acquire,
            True,
            timeout=DEFAULT_TIMEOUT,
            wait_for_set_completion=False,
        )

        async def complete_acquisition() -> None:
            # NOTE: possible race condition here between the callback from
            # set_and_wait_for_value and the detector state updating.
            await status
            state = await self.driver.detector_state.get_value()
            if state not in self.good_states:
                raise ValueError(
                    f"Final detector state {state.value} not "
                    "in valid end states: {self.good_states}"
                )

        return AsyncStatus(complete_acquisition())

    async def wait_for_idle(self):
        if self._arm_status and not self._arm_status.done:
            await self._arm_status
        self._arm_status = None


class AbstractAnalyserDetector(
    Device,
    Stageable,
    Triggerable,
    AsyncReadable,
    AsyncConfigurable,
    Generic[TAbstractAnalyserDriverIO],
):
    def __init__(self, prefix: str, name: str, driver: TAbstractAnalyserDriverIO):
        self.driver = driver
        self.controller = AnalyserController(driver=self.driver)

        self.per_scan_metadata: list[SignalR] = [
            self.driver.region_name,
            self.driver.excitation_energy,
            self.driver.energy_mode,
            self.driver.energy_step,
            self.driver.high_energy,
            self.driver.low_energy,
            self.driver.iterations,
            self.driver.slices,
            self.driver.step_time,
            self.driver.total_steps,
            self.driver.total_time,
            self.driver.lens_mode,
            self.driver.pass_energy,
            self.driver.energy_axis,
            self.driver.binding_energy_axis,
            self.driver.angle_axis,
        ]
        self.per_point_metadata: list[SignalR] = [
            self.driver.spectrum,
            self.driver.image,
            self.driver.total_intensity,
            self.driver.excitation_energy,
        ]

        super().__init__(name)

    @AsyncStatus.wrap
    async def trigger(self) -> None:
        await self.controller.arm()
        await self.controller.wait_for_idle()

    @AsyncStatus.wrap
    async def stage(self) -> None:
        """Make sure the detector is idle and ready to be used."""
        await asyncio.gather(self.controller.disarm())

    @AsyncStatus.wrap
    async def unstage(self) -> None:
        """Disarm the detector."""
        await asyncio.gather(self.controller.disarm())

    # PER_POINT
    async def read(self) -> dict[str, Reading]:
        data = await merge_gathered_dicts(
            [signal.read() for signal in self.per_point_metadata]
        )
        # prefix = self.driver.name + "-"
        # is_binding_energy = (
        #     await self.driver.energy_mode.get_value() == EnergyMode.BINDING
        # )
        # if is_binding_energy:
        #     del data[prefix + "energy_axis"]
        # else:
        #     del data[prefix + "binding_energy_axis"]
        return data

    async def describe(self) -> dict[str, DataKey]:
        data = await merge_gathered_dicts(
            [signal.describe() for signal in self.per_point_metadata]
        )
        # Correct the shape for image
        prefix = self.driver.name + "-"
        energy_size = len(await self.driver.energy_axis.get_value())
        angle_size = len(await self.driver.angle_axis.get_value())
        data[prefix + "image"]["shape"] = [angle_size, energy_size]
        return data

    # PER_SCAN
    async def read_configuration(self) -> dict[str, Reading]:
        for signal in self.per_scan_metadata:
            print(signal.source + ": " + str(await signal.get_value()))
        return await merge_gathered_dicts(
            [signal.read() for signal in self.per_scan_metadata]
        )

    async def describe_configuration(self) -> dict[str, DataKey]:
        return await merge_gathered_dicts(
            [signal.describe() for signal in self.per_scan_metadata]
        )
