import asyncio
from dataclasses import dataclass
from functools import cached_property

import numpy as np
from daq_config_server.client import ConfigClient
from daq_config_server.models.i15_1.xpdf_parameters import (
    TemperatureControllerParams,
)
from ophyd_async.core import (
    MovableLogic,
    Reference,
    SignalR,
    SignalRW,
    StandardMovable,
    StandardReadable,
    TimeoutCalculator,
    set_and_wait_for_other_value,
    soft_signal_rw,
)
from ophyd_async.core import StandardReadableFormat as Format
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.common.enums import ValveState
from dodal.devices.beamlines.i15_1.safe_or_beam_positioner import SafeOrBeamPositioner


@dataclass
class TemperatureMoveLogic(MovableLogic[float]):
    pneumatic: SignalR[ValveState]
    settle_time_s: SignalRW[float]

    # We could work this out better based on ramp rate but would need more calibration
    # to make sure it's accurate, for now an hour is fine
    TIMEOUT = 60 * 60

    async def stop(self):
        await self.setpoint.set(0)

    async def move(self, new_position: float, timeout: TimeoutCalculator) -> None:
        pneumatic_state = await self.pneumatic.get_value()
        if new_position > 0 and pneumatic_state != ValveState.OPEN:
            raise ValueError("Blower cannot be turned on pneumatic is not open")

        # If we're turning the blower off we do not need to wait as the temperature
        # reading is just the latent heat in the device and the sample is not being heated
        if new_position == 0:
            await self.setpoint.set(0)
        else:
            await set_and_wait_for_other_value(
                self.setpoint,
                new_position,
                self.readback,
                lambda v: bool(np.isclose(v, new_position)),
                timeout=self.TIMEOUT,
            )
            await asyncio.sleep(await self.settle_time_s.get_value())


class Temperature(StandardReadable, StandardMovable[float]):
    def __init__(
        self,
        prefix: str,
        pneumatic_pv: str,
        settle_time_s: Reference[SignalRW[float]],
    ) -> None:
        with self.add_children_as_readables(format=Format.HINTED_SIGNAL):
            self._temperature_rbv = epics_signal_r(float, f"{prefix}PV:RBV")

        with self.add_children_as_readables(format=Format.CONFIG_SIGNAL):
            self._temperature_sp = epics_signal_rw(float, f"{prefix}SP")
            self._pneumatic = epics_signal_r(ValveState, pneumatic_pv)

        self._settle_time_s = settle_time_s
        super().__init__()

    @cached_property
    def movable_logic(self) -> MovableLogic:
        return TemperatureMoveLogic(
            setpoint=self._temperature_sp,
            readback=self._temperature_rbv,
            pneumatic=self._pneumatic,
            settle_time_s=self._settle_time_s(),
        )


class Blower(SafeOrBeamPositioner):
    """Blows hot air on to the sample, can be moved out of the beam to allow room for
    a robot load.

    Temperatures are set in C. When a temperature is set the device will wait to reach
    that temperature and then wait a settle time as defined in `settle_time_s`. Setting
    a temperature of 0 will turn the blower off.

    For safety reasons the heater should only be turned on (set to a >0 temperature) if
    the given pneumatic is open to allow airflow.
    """

    def __init__(
        self,
        prefix: str,
        motion_pv: str,
        pneumatic_pv: str,
        config_client: ConfigClient,
        xpdf_parameters_path: str,
        name: str = "",
    ):
        self.ramp_rate_c_per_sec = epics_signal_rw(
            float, f"{prefix}RR", f"{prefix}RR:RBV"
        )

        self.settle_time_s = soft_signal_rw(float)

        with self.add_children_as_readables():
            self.temperature = Temperature(
                prefix, pneumatic_pv, Reference(self.settle_time_s)
            )

        super().__init__(motion_pv, config_client, xpdf_parameters_path, name)

    def get_config(self) -> TemperatureControllerParams:
        return self.get_full_config().blower
