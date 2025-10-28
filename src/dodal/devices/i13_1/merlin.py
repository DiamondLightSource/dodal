from collections.abc import Sequence

from ophyd_async.core import PathProvider, SignalR
from ophyd_async.epics import adcore

from dodal.common.beamlines.device_helpers import CAM_SUFFIX, HDF5_SUFFIX

from .merlin_controller import MerlinController


class Merlin(adcore.AreaDetector[MerlinController]):
    def __init__(
        self,
        prefix: str,
        path_provider: PathProvider,
        drv_suffix=CAM_SUFFIX,
        writer_cls: type[adcore.ADWriter] = adcore.ADHDFWriter,
        fileio_suffix=HDF5_SUFFIX,
        name: str = "",
        config_sigs: Sequence[SignalR] = (),
        plugins: dict[str, adcore.NDPluginBaseIO] | None = None,
    ):
        driver = adcore.ADBaseIO(prefix + drv_suffix)
        controller = MerlinController(driver)
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
