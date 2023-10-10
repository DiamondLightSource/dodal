from pathlib import Path

from ophyd_async.core import DeviceCollector
from ophyd_async.epics.areadetector import (
    ADDriver,
    HDFStreamerDet,
    NDFileHDF,
    TmpDirectoryProvider,
)
from ophyd_async.panda import PandA

from dodal.devices.athena.panda import FlyingPanda
from dodal.utils import BeamlinePrefix

BEAMLINE = "p38"
PREFIX: str = BeamlinePrefix(BEAMLINE).beamline_prefix
VISIT = "2023/cm33874-3"
D11_PV = "DI-DCAM-03"
D12_PV = "DI-DCAM-04"


def d11(name: str = "D11", sim: bool = False) -> HDFStreamerDet:
    d11_dir = TmpDirectoryProvider()
    d11_dir._directory = Path(f"/dls/{BEAMLINE}/data/{VISIT}/{name}")

    with DeviceCollector(sim=sim):
        d11_drv = ADDriver(f"{PREFIX}-{D11_PV}:DET:")
        d11_hdf = NDFileHDF(f"{PREFIX}-{D11_PV}:HDF5:")
        det = HDFStreamerDet(d11_drv, d11_hdf, d11_dir, name)
    return det


def d12(name: str = "D12", sim: bool = False) -> HDFStreamerDet:
    d12_dir = TmpDirectoryProvider()
    d12_dir._directory = Path(f"/dls/{BEAMLINE}/data/{VISIT}/{name}")

    with DeviceCollector(sim=sim):
        d12_drv = ADDriver(f"{PREFIX}-{D12_PV}:DET:")
        d12_hdf = NDFileHDF(f"{PREFIX}-{D12_PV}:HDF5:")
        det = HDFStreamerDet(d12_drv, d12_hdf, d12_dir, name)
    return det


def panda(name: str = "PANDA", sim: bool = False) -> FlyingPanda:
    with DeviceCollector(sim=sim):
        pbox = PandA("BL38P-PANDA")
        pbox.set_name(name)
    fp = FlyingPanda(pbox)
    return fp
