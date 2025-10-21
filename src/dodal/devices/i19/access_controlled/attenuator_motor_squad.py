from typing import Annotated, Any, Self

from ophyd_async.core import AsyncStatus
from pydantic import BaseModel, model_validator
from pydantic.types import PositiveInt, StringConstraints

from dodal.devices.i19.access_controlled.blueapi_device import (
    OpticsBlueAPIDevice,
)
from dodal.devices.i19.access_controlled.hutch_access import ACCESS_DEVICE_NAME

PermittedKeyStr = Annotated[str, StringConstraints(pattern="^[A-Za-z0-9-_]*$")]


class AttenuatorMotorPositionDemands(BaseModel):
    continuous_demands: dict[PermittedKeyStr, float] = {}
    indexed_demands: dict[PermittedKeyStr, PositiveInt] = {}

    @model_validator(mode="after")
    def no_keys_clash(self) -> Self:
        common_key_filter = filter(
            lambda k: k in self.continuous_demands, self.indexed_demands
        )
        common_key_count = sum(1 for _ in common_key_filter)
        if common_key_count < 1:
            return self
        else:
            ks: str = "key" if common_key_count == 1 else "keys"
            error_msg = (
                f"{common_key_count} common {ks} found in distinct motor demands"
            )
            raise ValueError(error_msg)

    def restful_format(self) -> dict[PermittedKeyStr, Any]:
        return self.continuous_demands | self.indexed_demands


class AttenuatorMotorSquad(OpticsBlueAPIDevice):
    """ I19-specific proxy device which requests absorber position changes in the x-ray attenuator.

    Sends REST call to blueapi controlling optics on the I19 cluster.
     The hutch in use is compared against the hutch which sent the REST call.
    Only the hutch in use will be permitted to execute a plan (requesting motor moves).
    As the two hutches are located in series, checking the hutch in use is necessary to \
    avoid accidentally operating optics devices from one hutch while the other has beam time.

    The name of the hutch that wants to operate the optics device is passed to the \
    access controlled device upon instantiation of the latter.

    For details see the architecture described in \
    https://github.com/DiamondLightSource/i19-bluesky/issues/30.
    """

    @AsyncStatus.wrap
    async def set(self, value: AttenuatorMotorPositionDemands):
        request_params = {
            "name": "operate_motor_squad_plan",
            "params": {
                "experiment_hutch": self._get_invoking_hutch(),
                "access_device": ACCESS_DEVICE_NAME,
                "attenuator_demands": value.restful_format(),
            },
            "instrument_session": self.instrument_session,
        }
        await super().set(request_params)
