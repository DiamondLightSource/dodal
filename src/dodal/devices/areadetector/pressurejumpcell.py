from collections.abc import Sequence

from ophyd_async.core import PathProvider, SignalR
from ophyd_async.epics.adcore import ADHDFWriter, ADWriter, AreaDetector, NDPluginBaseIO

from .pressurejumpcell_controller import (
    PRESSURE_CELL_READAOUT_TIME,
    PressureJumpCellController,
)
from .pressurejumpcell_io import PressureJumpCellDriverIO


class PressureJumpCellDetector(AreaDetector[PressureJumpCellController]):
    """
    Ophyd-async implementation of a Pressure Jump Cell ADC Detector for fast pressure jumps.
    The detector may be configured for an external trigger on the TTL Trig input.
    """

    def __init__(
        self,
        prefix: str,
        path_provider: PathProvider,
        readout_time: float = PRESSURE_CELL_READAOUT_TIME,
        drv_suffix="cam1:",
        adc_suffix="TRIG",
        writer_cls: type[ADWriter] = ADHDFWriter,
        fileio_suffix: str | None = None,
        name="",
        plugins: dict[str, NDPluginBaseIO] | None = None,
        config_sigs: Sequence[SignalR] = (),
    ):

        driver = PressureJumpCellDriverIO(prefix + drv_suffix)
        controller = PressureJumpCellController(driver, readout_time=readout_time)

        writer = writer_cls.with_io(
            prefix,
            path_provider,
            dataset_source=driver,
            fileio_suffix=fileio_suffix,
            plugins=plugins,
        )

        super().__init__(
            controller=controller,
            writer=writer,
            plugins=plugins,
            name=name,
            config_sigs=config_sigs,
        )

