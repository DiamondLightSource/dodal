from dodal.beamlines.beamline_utils import device_instantiation
from dodal.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.i19.one.diffractometer import Diffractometer
from dodal.devices.oav.oav_detector import OAV
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name, skip_device

_simulator_beamline_fallback = "s19_1"
BL = get_beamline_name(_simulator_beamline_fallback)
set_log_beamline(BL)
set_utils_beamline(BL)


def _check_for_simulation():
    return BL == _simulator_beamline_fallback


@skip_device(_check_for_simulation)
def diffractometer(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Diffractometer:
    return device_instantiation(
        device=Diffractometer,
        name="eh1_diffractometer",
        prefix="-MO",
        wait_for_connection=wait_for_connection,
        fake_with_ophyd_sim=fake_with_ophyd_sim,
    )


@skip_device(_check_for_simulation)
def off_axis_viewer(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> OAV:
    """Get the i19_1 Off axis viewer (OAV2) device
    instantiate it if it hasn't already been instantiated.
    If this is called when already instantiated on i19_1, then return the existent object.
    N.B. The mnemonic "on is one" helps distinguish on- and off- axis OAVs.
    """
    return device_instantiation(
        device=OAV,
        name="oav2",
        prefix="-DI-OAV-02:",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


@skip_device(_check_for_simulation)
def on_axis_viewer(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> OAV:
    """Get the i19_1 On axis viewer (OAV1) device
    instantiate it if it hasn't already been instantiated.
    If this is called when already instantiated on i19_1, then return the existent object.
    N.B. The mnemonic "on is one" helps distinguish on- and off- axis OAVs.
    """
    return device_instantiation(
        device=OAV,
        name="oav1",
        prefix="-DI-OAV-01:",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )
