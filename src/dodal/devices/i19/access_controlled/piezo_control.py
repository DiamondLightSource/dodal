from enum import StrEnum

from ophyd_async.core import AsyncStatus, StandardReadableFormat
from ophyd_async.epics.core import epics_signal_r

from dodal.devices.i19.access_controlled.blueapi_device import (
    HutchState,
    OpticsBlueAPIDevice,
)
from dodal.devices.i19.access_controlled.hutch_access import ACCESS_DEVICE_NAME


class FocusingMirrorName(StrEnum):
    VFM = "vfm"
    HFM = "hfm"


PIEZO_CONTROL_PLAN_NAME = "apply_voltage_to_piezo"


# NOTE This device is only meant to control the piezo. There should be a separate device
# to control the actual focusing mirror motors, as the two operations are often done
# independently.
class AccessControlledPiezoActuator(OpticsBlueAPIDevice):
    """I19-specific device to set a voltage on the focusing mirror piezoelectric
    actuator.

    This device will send a REST call to the blueapi instance controlling the optics
    hutch running on the I19 cluster, which will evaluate the current hutch in use vs
    the hutch sending the request and decide if the plan will be run or not.
    As the two hutches are located in series, checking the hutch in use is necessary to
    avoid accidentally operating the shutter from one hutch while the other has beamtime.

    The name of the hutch that wants to operate the shutter, as well as a commissioning
    directory to act as a placehlder for the instrument_session,should be passed to the
    device upon instantiation.

    A mirror type (vfm or hfm) also needs to be set upon instantiation so that the
    correct plan can be run and the correct optics device is injected.

    For details see the architecture described in
    https://diamondlightsource.github.io/i19-bluesky/main/explanations/decisions/0004-optics-blueapi-architecture.html
    """

    def __init__(
        self,
        prefix: str,
        mirror_type: FocusingMirrorName,
        hutch: HutchState,
        instrument_session: str = "",
        name: str = "",
    ):
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.readback = epics_signal_r(float, f"{prefix}AOFPITCH:RBV")
        self.mirror = mirror_type
        super().__init__(hutch=hutch, instrument_session=instrument_session, name=name)

    @AsyncStatus.wrap
    async def set(self, value: float):
        request_params = {
            "name": PIEZO_CONTROL_PLAN_NAME,
            "params": {
                "experiment_hutch": self._invoking_hutch,
                "access_device": ACCESS_DEVICE_NAME,
                "voltage_demand": value,
                "focus_mirror": self.mirror.value,
            },
            "instrument_session": self.instrument_session,
        }
        await super().set(request_params)
