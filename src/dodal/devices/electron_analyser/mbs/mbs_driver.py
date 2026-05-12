import asyncio
from typing import Generic

import numpy as np
from ophyd_async.core import (
    Array1D,
    AsyncStatus,
    SignalR,
    StandardReadableFormat,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.devices.electron_analyser.base.base_driver_io import (
    _PSU,
    AbstractAnalyserDriverIO,
)
from dodal.devices.electron_analyser.base.base_region import (
    TLensMode,
    TPassEnergy,
    TPsuMode,
)
from dodal.devices.electron_analyser.mbs.mbs_enums import AcquisitionMode
from dodal.devices.electron_analyser.mbs.mbs_region import MbsRegion


class MbsAnalyserDriverIO(
    AbstractAnalyserDriverIO[
        MbsRegion[TLensMode, TPsuMode, TPassEnergy],
        AcquisitionMode,
        TLensMode,
        TPsuMode,
        TPassEnergy,
    ],
    Generic[TLensMode, TPsuMode, TPassEnergy],
):
    def __init__(
        self,
        prefix: str,
        lens_mode_type: type[TLensMode],
        psu_mode_type: type[TPsuMode],
        pass_energy_type: type[TPassEnergy],
        psu_suffix: str = _PSU,
        name: str = "",
    ):
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.deflector_x = epics_signal_rw(float, prefix + "DeflX")

        super().__init__(
            prefix=prefix,
            acquisition_mode_type=AcquisitionMode,
            lens_mode_type=lens_mode_type,
            psu_mode_type=psu_mode_type,
            pass_energy_type=pass_energy_type,
            psu_suffix=psu_suffix,
            name=name,
        )

    def _create_angle_axis_signal(self, prefix: str) -> SignalR[Array1D[np.float64]]:
        return epics_signal_r(Array1D[np.float64], prefix + "LensScale_RBV")

    def _create_energy_axis_signal(self, prefix: str) -> SignalR[Array1D[np.float64]]:
        return epics_signal_r(Array1D[np.float64], prefix + "EScale_RBV")

    @AsyncStatus.wrap
    async def set(self, epics_region: MbsRegion[TLensMode, TPsuMode, TPassEnergy]):
        # What do we do about region name?
        coroutines = [
            self.acquisition_mode.set(epics_region.acquisition_mode),
            self.pass_energy.set(epics_region.pass_energy),
            self.lens_mode.set(epics_region.lens_mode),
            # Start stop and centre energy are always set even though start and stop are
            # used in swept and centre is used in fixed because the readback values are
            # saved into the data file.
            self.low_energy.set(epics_region.low_energy),
            self.high_energy.set(epics_region.high_energy),
            # Does this need to go in sub class?
            self.deflector_x.set(epics_region.deflector_x),
            self.acquire_time.set(epics_region.acquire_time),
            self.iterations.set(epics_region.iterations),
        ]
        if epics_region.acquisition_mode == AcquisitionMode.SWEPT:
            centre_energy = (epics_region.high_energy + epics_region.low_energy) / 2.0
            coroutines.append(self.centre_energy.set(centre_energy))

        await asyncio.gather(*coroutines)
