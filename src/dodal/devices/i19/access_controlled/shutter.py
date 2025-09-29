from ophyd_async.core import AsyncStatus, StandardReadableFormat
from ophyd_async.epics.core import epics_signal_r

from dodal.devices.hutch_shutter import ShutterDemand, ShutterState
from dodal.devices.i19.access_controlled.hutch_access import ACCESS_DEVICE_NAME
from dodal.devices.i19.access_controlled.optics_blueapi_device import (
    HutchState,
    OpticsBlueApiDevice,
)


class AccessControlledShutter(OpticsBlueApiDevice):
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

    def __init__(
        self,
        prefix: str,
        hutch: HutchState,
        instrument_session: str = "",
        name: str = "",
    ) -> None:
        # For instrument session addition to request parameters
        # see https://github.com/DiamondLightSource/blueapi/issues/1187
        super().__init__(hutch, name)
        self.instrument_session = instrument_session
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.shutter_status = epics_signal_r(ShutterState, f"{prefix}STA")

    @AsyncStatus.wrap
    async def set(self, value: ShutterDemand):
        invoking_hutch = self._get_invoking_hutch().value
        REQUEST_PARAMS = {
            "name": "operate_shutter_plan",
            "params": {
                "experiment_hutch": invoking_hutch,
                "access_device": ACCESS_DEVICE_NAME,
                "shutter_demand": value.value,
            },
            "instrument_session": self.instrument_session,
        }
        await super().set(REQUEST_PARAMS)
