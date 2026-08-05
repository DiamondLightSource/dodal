from functools import cached_property
from typing import Annotated, Self

from ophyd_async.core import AsyncStatus
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictFloat,
    StrictInt,
    model_validator,
)
from pydantic.types import StringConstraints

from dodal.devices.beamlines.i19.access_controlled.blueapi_device import (
    OpticsBlueAPIDevice,
)
from dodal.devices.beamlines.i19.access_controlled.hutch_access import (
    ACCESS_DEVICE_NAME,
)

PermittedKeyStr = Annotated[
    str, StringConstraints(pattern=r"^[_A-Za-z][A-Za-z0-9-_]*$")
]


class AttenuatorMotorPositions(BaseModel):
    """Motor positions for attentuators in the attenuation system, be they indices on a discrete steps motor or continuous positions on an axis, or axes.

    This is a validated dict which pairs off naming "tags" for each motor (e.g. "x" for a lateral x-axis motor or "w" for a filter wheel),
    with the corresponding int or float motor position ( or position demand / request ) as appropriate.

    Attributes:
        continuous_positions: dict contributions pairing names of motors against the discrete motor position (likely to be in mm)/
        discrete_indicecs: dict contributions pairing names of index stepping positioners against the discrete poisition index (e.g. for a filter wheel).

    Examples:
        Request for motor changes:
            {"x": 20.4} and {"w":3} might indicate a request to move x-axis to 20.4 mm and the wheel round to slot 3.

        Reporting of system motor positions (on say i19, where wheel index 1 is reserved for an EMPTY slot):
        {"x": 28.62, "y": 5.0} and {"w": 1} might indicate the resin wedge is at 28.62 mm, aluminium wedge is OUT, filter wheel at EMPTY (OUT)."
    """

    model_config = ConfigDict(frozen=True)

    continuous_positions: dict[PermittedKeyStr, StrictFloat | StrictInt] = Field(
        default_factory=dict, kw_only=True
    )
    discrete_indices: dict[PermittedKeyStr, Annotated[StrictInt, Field(gt=0)]] = Field(
        default_factory=dict, kw_only=True
    )

    @model_validator(mode="after")
    def no_keys_clash(self) -> Self:
        common_keys = set(self.continuous_positions).intersection(self.discrete_indices)
        common_key_count = sum(1 for _ in common_keys)
        if common_key_count < 1:
            return self
        else:
            ks: str = "key" if common_key_count == 1 else "keys"
            error_msg = f"Common {ks} found in distinct motor demands: {common_keys}"
            raise ValueError(error_msg)

    @cached_property
    def _cached_merged_validated_dict(
        self,
    ) -> dict[PermittedKeyStr, StrictInt | StrictFloat]:
        """Lazily evaluate the merged dict, post validation and cache for future use.

        Returns:
            The validated union of both discrete motor index and continuous motor position contributions.
        """
        return self.continuous_positions | self.discrete_indices

    def validated_and_complete(
        self,
    ) -> dict[PermittedKeyStr, StrictInt | StrictFloat]:
        """Reports back the validated combined position information.

        Returns:
            The validated union of both discrete motor index and continuous motor position contributions.
        """
        return self._cached_merged_validated_dict


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
                "attenuator_demands": value.validated_and_complete(),
            },
            "instrument_session": self.instrument_session,
        }
        await super().set(request_params)
