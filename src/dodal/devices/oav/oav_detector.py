from enum import IntEnum

from bluesky.protocols import Movable
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    AsyncStatus,
    LazyMock,
    SignalR,
    SignalRW,
    StandardReadable,
    derived_signal_r,
    soft_signal_rw,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.devices.areadetector.plugins.cam import Cam
from dodal.devices.oav.oav_parameters import (
    DEFAULT_OAV_WINDOW,
    OAVConfig,
    OAVConfigBase,
    OAVConfigBeamCentre,
)
from dodal.devices.oav.snapshots.snapshot import Snapshot
from dodal.devices.oav.snapshots.snapshot_with_grid import SnapshotWithGrid


class Coords(IntEnum):
    X = 0
    Y = 1


# Workaround to deal with the fact that beamlines may have slightly different string
# descriptions of the zoom level"
def _get_correct_zoom_string(zoom: str) -> str:
    if zoom.endswith("x"):
        zoom = zoom.strip("x")
    return zoom


class BaseZoomController(StandardReadable, Movable[str]):
    level: SignalRW[str]
    percentage: SignalRW[float]


class NullZoomController(BaseZoomController):
    def __init__(self):
        self.level = soft_signal_rw(str, "1.0x")
        self.percentage = soft_signal_rw(float, 100)
        super().__init__()

    @AsyncStatus.wrap
    async def set(self, value: str) -> None:
        if value != "1.0x":
            raise Exception("Attempting to set zoom level of a null zoom controller")
        else:
            await self.level.set(value, wait=True)


class ZoomController(BaseZoomController):
    """
    Device to control the zoom level. This should be set like
        o = OAV(name="oav")
        oav.zoom_controller.set("1.0x")

    Note that changing the zoom may change the AD wiring on the associated OAV, as such
    you should wait on any zoom changs to finish before changing the OAV wiring.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
        self.percentage = epics_signal_rw(float, f"{prefix}ZOOMPOSCMD")

        # Level is the string description of the zoom level e.g. "1.0x" or "1.0"
        self.level = epics_signal_rw(str, f"{prefix}MP:SELECT")
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, value: str):
        await self.level.set(value, wait=True)


class OAV(StandardReadable):
    """
    Class for oav device

    x_direction(int): Should only be 1 or -1, with 1 indicating the oav x direction is the same with motor x
    y_direction(int): Same with x_direction but for motor y
    z_direction(int): Same with x_direction but for motor z
    mjpg_x_size_pv(str): PV infix for x_size in mjpg
    mjpg_y_size_pv(str): PV infix for y_size in mjpg
    """

    beam_centre_i: SignalR[int]
    beam_centre_j: SignalR[int]

    def __init__(
        self,
        prefix: str,
        config: OAVConfigBase,
        name: str = "",
        mjpeg_prefix: str = "MJPG",
        zoom_controller: BaseZoomController | None = None,
        x_direction: int = -1,
        y_direction: int = -1,
        z_direction: int = 1,
        mjpg_x_size_pv: str = "ArraySize1_RBV",
        mjpg_y_size_pv: str = "ArraySize2_RBV",
    ):
        self.oav_config = config
        self._prefix = prefix
        self._name = name
        _bl_prefix = prefix.split("-")[0]

        if not zoom_controller:
            self.zoom_controller = ZoomController(
                f"{_bl_prefix}-EA-OAV-01:FZOOM:", name
            )
        else:
            self.zoom_controller = zoom_controller

        self.cam = Cam(f"{prefix}CAM:", name=name)
        with self.add_children_as_readables():
            self.grid_snapshot = SnapshotWithGrid(
                f"{prefix}{mjpeg_prefix}:", name, mjpg_x_size_pv, mjpg_y_size_pv
            )

        self.sizes = [self.grid_snapshot.x_size, self.grid_snapshot.y_size]
        with self.add_children_as_readables():
            self.x_direction = soft_signal_rw(int, x_direction, name="x_direction")
            self.y_direction = soft_signal_rw(int, y_direction, name="y_direction")
            self.z_direction = soft_signal_rw(int, z_direction, name="z_direction")

        with self.add_children_as_readables():
            self.microns_per_pixel_x = derived_signal_r(
                self._get_microns_per_pixel,
                zoom_level=self.zoom_controller.level,
                size=self.sizes[Coords.X],
                coord=soft_signal_rw(datatype=int, initial_value=Coords.X.value),
            )
            self.microns_per_pixel_y = derived_signal_r(
                self._get_microns_per_pixel,
                zoom_level=self.zoom_controller.level,
                size=self.sizes[Coords.Y],
                coord=soft_signal_rw(datatype=int, initial_value=Coords.Y.value),
            )
            self.snapshot = Snapshot(
                f"{self._prefix}{mjpeg_prefix}:",
                self._name,
            )

        super().__init__(name)

    def _read_current_zoom(self, _zoom: str) -> str:
        return _get_correct_zoom_string(_zoom)

    def _get_microns_per_pixel(self, zoom_level: str, size: int, coord: int) -> float:
        """Extracts the microns per x pixel and y pixel for a given zoom level."""
        _zoom = self._read_current_zoom(zoom_level)
        value = self.parameters[_zoom].microns_per_pixel[coord]
        return value * DEFAULT_OAV_WINDOW[coord] / size

    async def connect(
        self,
        mock: bool | LazyMock = False,
        timeout: float = DEFAULT_TIMEOUT,
        force_reconnect: bool = False,
    ):
        self.parameters = self.oav_config.get_parameters()

        return await super().connect(mock, timeout, force_reconnect)


class OAVBeamCentreFile(OAV):
    """
    OAV device that reads its beam centre values from a file. The config parameter
    must be a OAVConfigBeamCentre object, as this contains a filepath to where the beam
    centre values are stored.

    x_direction(int): Should only be 1 or -1, with 1 indicating the oav x direction is the same with motor x
    y_direction(int): Same with x_direction but for motor y
    z_direction(int): Same with x_direction but for motor z
    mjpg_x_size_pv(str): PV infix for x_size in mjpg
    mjpg_y_size_pv(str): PV infix for y_size in mjpg
    """

    def __init__(
        self,
        prefix: str,
        config: OAVConfigBeamCentre,
        name: str = "",
        mjpeg_prefix: str = "MJPG",
        zoom_controller: BaseZoomController | None = None,
        mjpg_x_size_pv: str = "ArraySize1_RBV",
        mjpg_y_size_pv: str = "ArraySize2_RBV",
        x_direction: int = -1,
        y_direction: int = -1,
        z_direction: int = 1,
    ):
        super().__init__(
            prefix=prefix,
            config=config,
            name=name,
            mjpeg_prefix=mjpeg_prefix,
            zoom_controller=zoom_controller,
            mjpg_x_size_pv=mjpg_x_size_pv,
            mjpg_y_size_pv=mjpg_y_size_pv,
            x_direction=x_direction,
            y_direction=y_direction,
            z_direction=z_direction,
        )

        with self.add_children_as_readables():
            self.beam_centre_i = derived_signal_r(
                self._get_beam_position,
                zoom_level=self.zoom_controller.level,
                size=self.sizes[Coords.X],
                coord=soft_signal_rw(datatype=int, initial_value=Coords.X.value),
            )
            self.beam_centre_j = derived_signal_r(
                self._get_beam_position,
                zoom_level=self.zoom_controller.level,
                size=self.sizes[Coords.Y],
                coord=soft_signal_rw(datatype=int, initial_value=Coords.Y.value),
            )
        # Set name so that new child signals get correct name
        self.set_name(self.name)

    def _get_beam_position(self, zoom_level: str, size: int, coord: int) -> int:
        """Extracts the beam location in pixels `xCentre` `yCentre`, for a requested \
        zoom level. """
        _zoom = self._read_current_zoom(zoom_level)
        value = self.parameters[_zoom].crosshair[coord]
        return int(value * size / DEFAULT_OAV_WINDOW[coord])


class OAVBeamCentrePV(OAV):
    """OAV device that reads its beam centre values from PVs."""

    def __init__(
        self,
        prefix: str,
        config: OAVConfig,
        name: str = "",
        mjpeg_prefix: str = "MJPG",
        zoom_controller: BaseZoomController | None = None,
        overlay_channel: int = 1,
    ):
        with self.add_children_as_readables():
            self.beam_centre_i = epics_signal_r(
                int, prefix + f"OVER:{overlay_channel}:CenterX"
            )
            self.beam_centre_j = epics_signal_r(
                int, prefix + f"OVER:{overlay_channel}:CenterY"
            )
        super().__init__(
            prefix=prefix,
            config=config,
            name=name,
            mjpeg_prefix=mjpeg_prefix,
            zoom_controller=zoom_controller,
        )
