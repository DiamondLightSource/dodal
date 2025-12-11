from enum import StrEnum

from ophyd_async.core import AsyncStatus, StandardReadableFormat
from ophyd_async.epics.core import epics_signal_r

from dodal.devices.i19.access_controlled.blueapi_device import (
    HutchState,
    OpticsBlueAPIDevice,
)
from dodal.devices.i19.access_controlled.hutch_access import ACCESS_DEVICE_NAME


class FocusingMirrorType(StrEnum):
    VFM = "vfm"
    HFM = "hfm"


PIEZO_CONTROL_PLAN_NAME = {
    FocusingMirrorType.VFM: "apply_voltage_to_vfm_piezo",
    FocusingMirrorType.HFM: "apply_voltage_to_hfm_piezo",
}


class AccessControlledPiezoActuator(OpticsBlueAPIDevice):
    def __init__(
        self,
        prefix: str,
        mirror_type: FocusingMirrorType,
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
            "name": PIEZO_CONTROL_PLAN_NAME[self.mirror],
            "params": {
                "experiment_hutch": self._invoking_hutch,
                "access_device": ACCESS_DEVICE_NAME,
                "voltage_demand": value,
            },
            "instrument_session": self.instrument_session,
        }
        await super().set(request_params)
