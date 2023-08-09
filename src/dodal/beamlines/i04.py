from dodal.beamlines.beamline_utils import device_instantiation
from dodal.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.ipin import IPin
from dodal.devices.lower_gonio_stages import GonioLowerStages
from dodal.devices.motors import XYZPositioner
from dodal.devices.smargon import Smargon
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name

BL = get_beamline_name("s04")
set_log_beamline(BL)
set_utils_beamline(BL)


def smargon(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Smargon:
    """Get the i04 Smargon device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        Smargon,
        "smargon",
        "-MO-SGON-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def lower_gonio_stages(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> XYZPositioner:
    """Get the i04 lower_gonio_stages device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        XYZPositioner,
        "lower_gonio_stages",
        "-MO-GONIO-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def sample_delivery_system(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> XYZPositioner:
    """Get the i04 sample_delivery_system device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        XYZPositioner,
        "sample_delivery_system",
        "-MO-SDE-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def ipin(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> IPin:
    """Get the i04 ipin device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        IPin,
        "ipin",
        "-EA-PIN-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )
