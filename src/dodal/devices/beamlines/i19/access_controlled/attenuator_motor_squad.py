from ophyd_async.core import AsyncStatus

from dodal.devices.beamlines.i19.access_controlled.blueapi_device import (
    OpticsBlueAPIDevice,
)
from dodal.devices.beamlines.i19.access_controlled.hutch_access import (
    ACCESS_DEVICE_NAME,
)
from dodal.devices.beamlines.i19.attenuator_motor_positions import (
    AttenuatorMotorPositions,
)


class AttenuatorMotorSquad(OpticsBlueAPIDevice):
    """I19-specific proxy device which requests absorber position changes in the
    x-ray attenuator.

    Sends REST call to blueapi controlling optics on the I19 cluster.
    The hutch in use is compared against the hutch which sent the REST call.
    Only the hutch in use will be permitted to execute a plan (requesting motor moves).
    As the two hutches are located in series, checking the hutch in use is necessary to
    avoid accidentally operating optics devices from one hutch while the other has beam
    time.

    The name of the hutch that wants to operate the optics device is passed to the
    access controlled device upon instantiation of the latter.

    For details see the architecture described in
    https://github.com/DiamondLightSource/i19-bluesky/issues/30.
    """

    @AsyncStatus.wrap
    async def set(self, value: AttenuatorMotorPositions):
        request_params = {
            "name": "operate_motor_squad_plan",
            "params": {
                "experiment_hutch": self._invoking_hutch,
                "access_device": ACCESS_DEVICE_NAME,
                "attenuator_demands": value.validated_and_complete,
            },
            "instrument_session": self.instrument_session,
        }
        await super().set(request_params)
