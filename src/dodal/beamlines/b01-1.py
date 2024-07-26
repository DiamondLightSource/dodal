from ophyd_async.core import StaticDirectoryProvider
from ophyd_async.panda import HDFPanda

from dodal.common.beamlines.beamline_utils import (
    device_instantiation,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.webcam import Webcam
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name

# BL = get_beamline_name("BL01C")
BL = "c01"
set_log_beamline(BL)
set_utils_beamline(BL)


static_directory_provider = StaticDirectoryProvider("/tmp/bluesky_test_static")
# set_directory_provider(PandASubdirectoryProvider())



def panda(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> HDFPanda:
    """Get the i03 panda_fast_grid_scan device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    This is used instead of the zebra_fast_grid_scan device when using the PandA.
    """
    return device_instantiation(
        device_factory=HDFPanda,
        name="panda",
        prefix="-EA-PANDA-01-0:",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
        directory_provider=static_directory_provider,
    )


# @skip_device(lambda: BL == "s03")
# def synchrotron(
#     wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
# ) -> Synchrotron:
#     """Get the i03 synchrotron device, instantiate it if it hasn't already been.
#     If this is called when already instantiated in i03, it will return the existing object.
#     """
#     return device_instantiation(
#         Synchrotron,
#         "synchrotron",
#         "",
#         wait_for_connection,
#         fake_with_ophyd_sim,
#         bl_prefix=False,
#     )

# def panda(
#     wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
# ) -> HDFPanda:
#     """Get the i03 panda device, instantiate it if it hasn't already been.
#     If this is called when already instantiated in i03, it will return the existing object.
#     """
#     return device_instantiation(
#         HDFPanda,
#         "panda",
#         "-EA-PANDA-01:",
#         wait_for_connection,
#         fake_with_ophyd_sim,
#         directory_provider=get_directory_provider(),
#     )


def webcam(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Webcam:
    """Get the i03 webcam, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        Webcam,
        "webcam",
        "",
        wait_for_connection,
        fake_with_ophyd_sim,
        url="http://i03-webcam1/axis-cgi/jpg/image.cgi",
    )


# def manta(
#     wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
# ) -> AravisDetector:
#     return device_instantiation(
#         AravisDetector,
#         "manta",
#         "-DI-DCAM-02:",
#         wait_for_connection,
#         fake_with_ophyd_sim,
#         directory_provider=static_directory_provider,
#     )
