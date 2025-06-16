from pathlib import Path  # noqa
from ophyd_async.fastcs.panda import HDFPanda

from dodal.common.beamlines.beamline_utils import (
    device_factory,
    get_path_provider,
    set_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.visit import RemoteDirectoryServiceClient, StaticVisitPathProvider
from ophyd_async.fastcs.eiger import EigerDetector
from ophyd_async.core import DeviceVector
from ophyd_async.epics.eiger._odin_io import OdinNode

from dodal.devices.linkam3 import Linkam3
from dodal.devices.slits import Slits
from dodal.devices.synchrotron import Synchrotron

from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("b21")
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_utils_beamline(BL)

# Currently we must hard-code the visit, determining the visit at runtime requires
# infrastructure that is still WIP.
# Communication with GDA is also WIP so for now we determine an arbitrary scan number
# locally and write the commissioning directory. The scan number is not guaranteed to
# be unique and the data is at risk - this configuration is for testing only.
set_path_provider(
    StaticVisitPathProvider(
        BL,
        Path("/dls/b21/data/2025/cm40642-3/bluesky"),
        client=RemoteDirectoryServiceClient(f"http://{BL}-control:8088/api"),
    )
)


# TODO: https://github.com/bluesky/ophyd-async/issues/923
# To be able to specify the number of OdinNodes Odin, and then on the EigerDetector
@device_factory()
def saxs() -> EigerDetector:
    odin_suffix = "-EA-EIGER-01:OD:"
    node_prefix = PREFIX.beamline_prefix + odin_suffix

    saxs_detector = EigerDetector(
        prefix=PREFIX.beamline_prefix,
        path_provider=get_path_provider(),
        drv_suffix="-EA-EIGER-01:",
        hdf_suffix=odin_suffix,
    )

    # TODO: https://github.com/DiamondLightSource/dodal/issues/1287
    saxs_detector.odin.nodes = DeviceVector(
        {i: OdinNode(f"{node_prefix[:-1]}{i + 1}:") for i in range(1)}
    )

    return saxs_detector


@device_factory(skip=True)
def waxs() -> EigerDetector:
    return EigerDetector(
        prefix=PREFIX.beamline_prefix,
        path_provider=get_path_provider(),
        drv_suffix="-EA-EIGER-02:",
        hdf_suffix="-EA-EIGER-02:OD:",
    )


@device_factory()
def panda1() -> HDFPanda:
    return HDFPanda(
        prefix=f"{PREFIX.beamline_prefix}-EA-PANDA-01:",
        path_provider=get_path_provider(),
    )


@device_factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@device_factory()
def slits_1() -> Slits:
    return Slits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-01:")


@device_factory()
def slits_2() -> Slits:
    return Slits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-02:")


@device_factory()
def slits_3() -> Slits:
    return Slits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-03:")


"""
Slits 4 was removed from B21 after the camera length was fixed, it is not used anymore.
"""


@device_factory()
def slits_5() -> Slits:
    return Slits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-05:")


@device_factory()
def slits_6() -> Slits:
    return Slits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-06:")


@device_factory()
def slits_7() -> Slits:
    """
    Compact JJ slits device is used for B21 slits 7. PV's operate in same way
    but physically different to other slits, and uses X:GAP nomenclature.
    """
    return Slits(
        prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-07:",
        x_gap="X:GAP",
        y_gap="Y:GAP",
        x_centre="X:CENTRE",
        y_centre="Y:CENTRE",
    )


@device_factory(skip=True)
def linkam() -> Linkam3:
    return Linkam3(prefix=f"{PREFIX.beamline_prefix}-EA-HPLC-01:")


# TODO: https://github.com/DiamondLightSource/dodal/issues/1286
# def dmm() -> DMM: #b21 uses a dmm so
#     return DMM()
