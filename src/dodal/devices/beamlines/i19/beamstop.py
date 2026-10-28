from daq_config_server.client import ConfigClient
from daq_config_server.models import beamline_parameters_to_dict
from ophyd_async.core import AsyncStatus, StandardReadable, StrictEnum
from ophyd_async.epics.core import epics_signal_rw, epics_signal_x

from dodal.common.enums import InOutUpper
from dodal.devices.motors import XYZStage

BEAMSTOP_IN_KEY = "beamstop_inbeam_x"
BEAMSTOP_OUT_KEY = "beamstop_outbeam_x"


class HomeGroup(StrictEnum):
    NONE = "none"
    ALL = "ALL"
    X = "X"
    Y = "Y"
    Z = "Z"


class HomingControl(StandardReadable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.homing_group = epics_signal_rw(HomeGroup, f"{prefix}:HMGRP")
        self.home = epics_signal_x(f"{prefix}:HOME")
        super().__init__(name)


class BeamStop(XYZStage):
    def __init__(
        self,
        prefix: str,
        beamline_parameters: str,
        config_client: ConfigClient,
        name: str = "",
    ) -> None:
        self._beamline_parameters = beamline_parameters
        self._config_client = config_client
        self.homing = HomingControl(f"{prefix}HM", name)

        super().__init__(prefix, name)

    # Temorary step until
    # https://github.com/DiamondLightSource/daq-config-server/pull/219 is merged
    # and released. After that, get_file_contents should be enough.
    def _read_beamline_parameters(self) -> str:
        return self._config_client.get_file_contents(self._beamline_parameters)

    def _get_position_from_beamline_parameters(self, key: str) -> float:
        params = beamline_parameters_to_dict(self._read_beamline_parameters())
        return params[key]

    @AsyncStatus.wrap
    async def set(self, value: InOutUpper):
        params_key = BEAMSTOP_IN_KEY if value is InOutUpper.IN else BEAMSTOP_OUT_KEY
        x_position = self._get_position_from_beamline_parameters(params_key)
        await self.x.set(x_position)
