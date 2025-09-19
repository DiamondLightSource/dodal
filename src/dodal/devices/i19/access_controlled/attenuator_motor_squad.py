from typing import Annotated, Any

from ophyd_async.core import AsyncStatus
from pydantic import BaseModel, field_validator
from pydantic.types import PositiveInt, StringConstraints

from dodal.devices.i19.access_controlled.hutch_access import ACCESS_DEVICE_NAME
from dodal.devices.i19.access_controlled.optics_blueapi_device import (
    OpticsBlueApiDevice,
)

PermittedKeyStr = Annotated[str, StringConstraints(pattern="^[A-Za-z0-9-_]*$")]


class AttenuatorMotorPositionDemands(BaseModel):
    continuous_demands: dict[PermittedKeyStr, float] = {}
    indexed_demands: dict[PermittedKeyStr, PositiveInt] = {}

    @field_validator("indexed_demands")
    def no_keys_clash(cls, indexed_demands, values, **kwargs):
        if len(indexed_demands) < 1:
            return indexed_demands
        other_demands = values["continuous_demands"]
        for key in indexed_demands:
            if key in other_demands:
                message = f"Attenuator Position Demand Key clash: {key}. Require distinct keys for axis names on continuous motors and indexed positions."
                raise ValueError(message)
        return indexed_demands

    def restful_format(self) -> dict[PermittedKeyStr, Any]:
        combined: dict[PermittedKeyStr, Any] = {}
        combined.update(self.continuous_demands)
        combined.update(self.indexed_demands)
        return combined


class AttenuatorMotorSquad(OpticsBlueApiDevice):
    """ I19-specific proxy device which requests absorber position changes in the x-ray attenuator.

    Sends REST call to blueapi controlling optics on the I19 cluster.
     The hutch in use is compared against the hutch which sent the REST call.
    Only the hutch in use will be permitted to execute a plan (requesting motor moves).
    As the two hutches are located in series, checking the hutch in use is necessary to \
    avoid accidentally operating optics devices from one hutch while the other has beam time.

    The name of the hutch that wants to operate the optics device is passed to the \
    access controlled device upon instantiation of the latter.

    Nomenclature:
    Note this class was originally called
        -MotorSet
        ( but objections were based on "set" being an overloaded word )

        -Gang might have worked,
        ( but a gang of mechanical devices are able to be mechanically coupled
        and move together; whereas the motors here are completely mutually independent )

        -Clique
        ( as in a set of friends, is an accurate choice, is unlikely to be overloaded, just sounds pretentious).

    For details see the architecture described in \
    https://github.com/DiamondLightSource/i19-bluesky/issues/30.
    """

    @AsyncStatus.wrap
    async def set(self, value: AttenuatorMotorPositionDemands):
        invoking_hutch = str(self._get_invoking_hutch().value)
        request_params = {
            "name": "operate_motor_clique_plan",
            "params": {
                "experiment_hutch": invoking_hutch,
                "access_device": ACCESS_DEVICE_NAME,
                "attenuator_demands": value.restful_format(),
            },
        }
        await super().set(request_params)
