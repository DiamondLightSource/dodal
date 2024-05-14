from dodal.devices.slits import Slits
from dodal.utils import skip_device

from .beamline_utils import device_instantiation


@skip_device()
def numbered_slits(
    slit_number: int = 1,
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> Slits:
    """
    Create a slits object following the {beamline}-AL-SLITS-{slit_number} PV
    convention

    Args:
        slit_number: The number assigned to the slits in the control system, usually
        its position in the assembly. Defaults to 1.
        wait_for_connection: Require connection on instantiation. Defaults to True.
        fake_with_ophyd_sim: Make a fake device. Defaults to False.

    Returns:
        Slits: A new slits object
    """

    return device_instantiation(
        Slits,
        f"s{slit_number}_slit_gaps",
        f"-AL-SLITS-{slit_number:02}:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )
