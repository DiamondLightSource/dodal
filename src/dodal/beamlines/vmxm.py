from dodal.beamlines.beamline_utils import device_instantiation
from dodal.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.eiger import EigerDetector
from dodal.devices.fast_grid_scan import FastGridScan
from dodal.devices.zebra import Zebra
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name, skip_device

SIM_BEAMLINE_NAME = "svmxm"

BL = get_beamline_name(SIM_BEAMLINE_NAME)
set_log_beamline(BL)
set_utils_beamline(BL)


@skip_device(lambda: BL == SIM_BEAMLINE_NAME)
def eiger(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> EigerDetector:
    """Get the vmxm eiger device, instantiate it if it hasn't already been.
    If this is called when already instantiated in vmxm, it will return the existing object.
    """
    return device_instantiation(
        device_factory=EigerDetector,
        name="eiger",
        prefix="-EA-EIGER-01:",
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


@skip_device(lambda: BL == SIM_BEAMLINE_NAME)
def fast_grid_scan(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> FastGridScan:
    """Get the vmxm fast_grid_scan device, instantiate it if it hasn't already been.
    If this is called when already instantiated in vmxm, it will return the existing object.
    """
    return device_instantiation(
        device_factory=FastGridScan,
        name="fast_grid_scan",
        prefix="-MO-SAMP-11:FGS:",  # TODO: currently needs Pxxxx prefixes in EPICS on VMXm, ask controls if we can alias to versions without these prefixes?
        wait=wait_for_connection,
        fake=fake_with_ophyd_sim,
    )


@skip_device(lambda: BL == SIM_BEAMLINE_NAME)
def zebra(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> Zebra:
    """Get the vmxm zebra device, instantiate it if it hasn't already been.
    If this is called when already instantiated in vmxm, it will return the existing object.
    """
    return device_instantiation(
        Zebra,
        "zebra",
        "-EA-ZEBRA-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )
