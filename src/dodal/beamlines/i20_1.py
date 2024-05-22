from dodal.common.beamlines.beamline_utils import device_instantiation
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.turbo_slit import TurboSlit
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name

BL = get_beamline_name("i20_1")
set_log_beamline(BL)
set_utils_beamline(BL)


def turbo_slit(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> TurboSlit:
    """
    turboslit for selecting energy from the polychromator
    """

    return device_instantiation(
        TurboSlit,
        prefix="-OP-PCHRO-01:TS:",
        name="turbo_slit",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )
