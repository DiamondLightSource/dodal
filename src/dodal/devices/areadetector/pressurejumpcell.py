from typing import get_args

from bluesky.protocols import HasHints, Hints

from ophyd_async.core import PathProvider, StandardDetector
from ophyd_async.epics import adcore

from .pressurejumpcell_controller import PressureJumpCellController
from .pressurejumpcell_io import PressureJumpCellDriverIO, PressureJumpCellAdcIO


class PressureJumpCellDetector(StandardDetector, HasHints):
    """
    Ophyd-async implementation of a Pressure Jump Cell ADC Detector for fast pressure jumps.
    The detector may be configured for an external trigger on the TTL Trig input.
    """

    _controller: PressureJumpCellController
    _writer: adcore.ADHDFWriter

    def __init__(
        self,
        prefix: str,
        path_provider: PathProvider,
        drv_suffix="cam1:",
        adc_suffix="TRIG",
        hdf_suffix="HDF1:",
        name="",
    ):
        self.drv = PressureJumpCellDriverIO(prefix + drv_suffix)
        self.adc = PressureJumpCellAdcIO(prefix + adc_suffix)
        self.hdf = adcore.NDFileHDFIO(prefix + hdf_suffix)

        super().__init__(
            PressureJumpCellController(self.drv, self.adc),
            adcore.ADHDFWriter(
                self.hdf,
                path_provider,
                lambda: self.name,
                adcore.ADBaseDatasetDescriber(self.drv),
            ),
            config_sigs=(self.drv.acquire_time,),
            name=name,
        )

    @property
    def hints(self) -> Hints:
        return self._writer.hints
