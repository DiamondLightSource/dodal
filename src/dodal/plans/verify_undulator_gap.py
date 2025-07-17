from typing import Protocol, runtime_checkable

from bluesky import plan_stubs as bps

from dodal.devices.common_dcm import BaseDCM
from dodal.devices.undulator import Undulator


@runtime_checkable
class CheckUndulatorDevices(Protocol):
    undulator: Undulator
    dcm: BaseDCM


def verify_undulator_gap(devices: CheckUndulatorDevices):
    """Verify Undulator gap is correct - it may not be after a beam dump"""

    energy_in_kev = yield from bps.rd(devices.dcm.energy_in_kev.user_readback)
    yield from bps.abs_set(devices.undulator, energy_in_kev, wait=True)
