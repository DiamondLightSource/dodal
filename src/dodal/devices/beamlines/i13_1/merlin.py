from ophyd_async.core import PathProvider
from ophyd_async.epics import adcore

from dodal.common.beamlines.device_helpers import CAM_SUFFIX, HDF5_SUFFIX
from dodal.devices.beamlines.i13_1.merlin_controller import (
    MerlinArmLogic,
    MerlinTriggerLogic,
)


class Merlin(adcore.AreaDetector):
    def __init__(
        self,
        prefix: str,
        path_provider: PathProvider,
        driver_suffix=CAM_SUFFIX,
        writer_suffix=HDF5_SUFFIX,
        name: str = "",
    ):
        self.driver = adcore.ADBaseIO(prefix + driver_suffix)
        self.hdf = adcore.NDFileHDF5IO(prefix + writer_suffix)
        super().__init__(
            prefix=prefix,
            driver=self.driver,
            arm_logic=MerlinArmLogic(self.driver),
            trigger_logic=MerlinTriggerLogic(self.driver),
            path_provider=path_provider,
            writer_suffix=writer_suffix,
            writer_type=adcore.ADWriterType.HDF,
            config_sigs=(self.driver.acquire_period, self.driver.acquire_time),
            name=name,
        )
