from abc import abstractmethod

from bluesky.protocols import Movable
from daq_config_server import ConfigClient
from daq_config_server.models.i15_1.xpdf_parameters import (
    TemperatureControllerParams,
    TemperatureControllersConfig,
)
from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
    StrictEnum,
)
from ophyd_async.epics.motor import Motor


class SafeOrBeamPosition(StrictEnum):
    SAFE = "Safe"
    BEAM = "Beam"


class SafeOrBeamPositioner(StandardReadable, Movable[SafeOrBeamPosition]):
    def __init__(
        self, prefix: str, config_client: ConfigClient, xpdf_parameters_path: str
    ):
        self.config_client = config_client
        self.xpdf_parameters_path = xpdf_parameters_path
        with self.add_children_as_readables():
            self.motor = Motor(prefix=prefix)
        super().__init__(prefix)

    @AsyncStatus.wrap
    async def set(self, value: SafeOrBeamPosition):
        if value == SafeOrBeamPosition.SAFE:
            await self.motor.set(self._safe_position)
        elif value == SafeOrBeamPosition.BEAM:
            await self.motor.set(self._beam_position)

    def get_full_config(self):
        return self.config_client.get_file_contents(
            self.xpdf_parameters_path,
            desired_return_type=TemperatureControllersConfig,
            force_parser=TemperatureControllersConfig.from_xpdf_parameters,
        )

    @abstractmethod
    def get_config(self) -> TemperatureControllerParams: ...

    @property
    def _safe_position(self) -> float:
        return self.get_config().safe_position

    @property
    def _beam_position(self) -> float:
        return self.get_config().beam_position
