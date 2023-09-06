from dodal.beamlines.beamline_utils import device_instantiation
from dodal.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.attenuator import Attenuator
from dodal.devices.beamstop import BeamStop
from dodal.devices.DCM import DCM
from dodal.devices.flux import Flux
from dodal.devices.i04.transfocator import Transfocator
from dodal.devices.ipin import IPin
from dodal.devices.motors import XYZPositioner
from dodal.devices.sample_shutter import SampleShutter
from dodal.devices.smargon import Smargon
from dodal.devices.xbpm_feedback import XBPMFeedback
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


def gonio_positioner(
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


def beamstop(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> BeamStop:
    """Get the i04 beamstop device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        BeamStop,
        "beamstop",
        "",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def sample_shutter(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> SampleShutter:
    """Get the i04 sample shutter device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        SampleShutter,
        "sample_shutter",
        "-EA-SHTR-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def attenuator(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Attenuator:
    """Get the i04 attenuator device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        Attenuator,
        "attenuator",
        "-EA-ATTN-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def transfocator(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Transfocator:
    """Get the i04 transfocator device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        Transfocator,
        "transfocator",
        "-MO-FSWT-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def xbpm_feedback(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> XBPMFeedback:
    """Get the i04 xbpm_feedback device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        XBPMFeedback,
        "xbpm_feedback",
        "",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def flux(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> Flux:
    """Get the i04 flux device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        Flux,
        "flux",
        "-MO-FLUX-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def dcm(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> DCM:
    """Get the i04 DCM device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i04, it will return the existing object.
    """
    return device_instantiation(
        DCM,
        "dcm",
        "",
        wait_for_connection,
        fake_with_ophyd_sim,
    )
