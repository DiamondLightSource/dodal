from typing import Any

from ophyd_async.core import AsyncStatus

from dodal.devices.i19.access_controlled.hutch_access import ACCESS_DEVICE_NAME
from dodal.devices.i19.access_controlled.optics_blueapi_device import (
    OpticsBlueApiDevice,
)


class AttenuatorPositionDemand:
    @staticmethod
    def _ensure_no_dict_k_is_none(d: dict[str, Any], msg: str) -> None:
        if any(k is None for k in d.keys()):
            raise ValueError(msg)

    @staticmethod
    def _ensure_no_dict_v_is_none(d: dict[str, Any], msg: str) -> None:
        if any(v is None for v in d.values()):
            raise ValueError(msg)

    @staticmethod
    def _validate_dict(d: dict[str, Any], motor_type: str):
        k_msg = f"Missing attenuator motor axis label for {motor_type}"
        AttenuatorPositionDemand._ensure_no_dict_k_is_none(d, k_msg)
        v_msg = f"Missing attenuator position demand value for {motor_type}"
        AttenuatorPositionDemand._ensure_no_dict_v_is_none(d, v_msg)

    @staticmethod
    def _ensure_dicts_share_no_common_k(a: dict[str, float], b: dict[str, int]) -> None:
        clashes_detected = filter(lambda k: k in a, b)
        if any(clashes_detected):
            msg_template: str = "Clashing keys in common between wheel and wedge for attenuation position demand: {}"
            reiterated = filter(lambda k: k in a, b)
            clashes = ",".join(reiterated)
            msg: str = msg_template.format(clashes)
            raise ValueError(msg)

    def __init__(
        self,
        continuous_motor_position_demands: dict[str, float],
        indexed_motor_position_demands: dict[str, int],
    ) -> None:
        self._validate_input(
            continuous_motor_position_demands, indexed_motor_position_demands
        )
        combined_demand: dict[str, Any] = {}
        combined_demand.update(continuous_motor_position_demands)
        combined_demand.update(indexed_motor_position_demands)
        self.demands = combined_demand

    def restful_format(self) -> dict[str, Any]:
        return self.demands.copy()

    def _validate_input(
        self,
        continuous_motor_position_demands: dict[str, float],
        indexed_motor_position_demands: dict[str, int],
    ):
        AttenuatorPositionDemand._validate_dict(
            continuous_motor_position_demands, "continuous motor"
        )
        AttenuatorPositionDemand._validate_dict(
            indexed_motor_position_demands, "indexed motor"
        )
        AttenuatorPositionDemand._ensure_dicts_share_no_common_k(
            continuous_motor_position_demands, indexed_motor_position_demands
        )


class AttenuatorMotorClique(OpticsBlueApiDevice):
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
    async def set(self, value: AttenuatorPositionDemand):
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
