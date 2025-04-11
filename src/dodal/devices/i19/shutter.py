from ophyd_async.core import AsyncStatus, StandardReadableFormat
from ophyd_async.epics.core import epics_signal_r

from dodal.devices.hutch_shutter import ShutterDemand, ShutterState
from dodal.devices.i19.blueapi_device import HutchState, OpticsBlueAPIDevice
from dodal.devices.i19.hutch_access import ACCESS_DEVICE_NAME


class AccessControlledShutter(OpticsBlueAPIDevice):
    """ I19-specific device to operate the hutch shutter.

    This device will send a REST call to the blueapi instance controlling the optics \
    hutch running on the I19 cluster, which will evaluate the current hutch in use vs \
    the hutch sending the request and decide if the plan will be run or not.
    As the two hutches are located in series, checking the hutch in use is necessary to \
    avoid accidentally operating the shutter from one hutch while the other has beamtime.

    The name of the hutch that wants to operate the shutter should be passed to the \
    device upon instantiation.

    For details see the architecture described in \
    https://github.com/DiamondLightSource/i19-bluesky/issues/30.
    """

    def __init__(self, prefix: str, hutch: HutchState, name: str = "") -> None:
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.shutter_status = epics_signal_r(ShutterState, f"{prefix}STA")
        self.hutch_request = hutch
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: ShutterDemand):
        REQUEST_PARAMS = {
            "name": "operate_shutter_plan",
            "params": {
                "experiment_hutch": self.hutch_request.value,
                "access_device": ACCESS_DEVICE_NAME,
                "shutter_demand": value.value,
            },
        }
        await super().set(REQUEST_PARAMS)
