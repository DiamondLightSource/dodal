from ophyd_async.panda import PandA

from dodal.beamlines.beamline_utils import device_instantiation, get_directory_provider
from dodal.beamlines.beamline_utils import set_beamline as set_utils_beamline

# from dodal.devices.areadetector import AdAravisDetector
from dodal.devices.areadetector.adaravis import SumHDFAravisDetector

# from dodal.devices.linkam3 import Linkam3
from dodal.devices.tetramm import TetrammDetector
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name

BL = get_beamline_name("p38")
set_log_beamline(BL)
set_utils_beamline(BL)


def d3(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> SumHDFAravisDetector:
    return device_instantiation(
        SumHDFAravisDetector,
        "D3",
        "-DI-DCAM-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        directory_provider=get_directory_provider(),
    )


# FIXME: Requires implementation, currently disconnected
# def d4(
#     wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
# ) ->


# FIXME: Currently disconnected
# def d11(
#     wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
# ) -> SumHDFAravisDetector:
#     return device_instantiation(
#         SumHDFAravisDetector,
#         "D11",
#         "-DI-DCAM-03:",
#         wait_for_connection,
#         fake_with_ophyd_sim,
#         directory_provider=get_directory_provider(),
#     )


def d12(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> SumHDFAravisDetector:
    return device_instantiation(
        SumHDFAravisDetector,
        "D12",
        "-DI-DCAM-04:",
        wait_for_connection,
        fake_with_ophyd_sim,
        directory_provider=get_directory_provider(),
    )


# FIXME: Requires implementation, currently disconnected
# def d13(
#     wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
# ) ->


# def linkam(
#     wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
# ) -> Linkam3:
#     return device_instantiation(
#         Linkam3, "linkam", "-EA-LINKM-02:", wait_for_connection, fake_with_ophyd_sim
#     )


# FIXME: Times out
def tetramm(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> TetrammDetector:
    return device_instantiation(
        TetrammDetector,
        "tetramm",
        "-EA-XBPM-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
        directory_provider=get_directory_provider(),
    )


def panda1(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> PandA:
    "Panda-01: Running as a python soft-ioc in Kubernetes. Hooked up to the TetrAMM"
    return device_instantiation(
        PandA, "panda1", "-EA-PANDA-01:", wait_for_connection, fake_with_ophyd_sim
    )


# FIXME: Times out
# def panda2(
#     wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
# ) -> PandA:
#     return device_instantiation(
#         PandA,
#         "panda2",
#         "-EA-PANDA-02:",
#         wait_for_connection,
#         fake_with_ophyd_sim,
#     )


# FIXME: Currently disconnected
# def panda3(
#     wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
# ) -> PandA:
#     return device_instantiation(
#         PandA, "panda3", "-EA-PANDA-02:", wait_for_connection, fake_with_ophyd_sim
#     )
