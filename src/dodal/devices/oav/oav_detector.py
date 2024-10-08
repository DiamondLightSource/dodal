# type: ignore # OAV will soon be ophyd-async, see https://github.com/DiamondLightSource/dodal/issues/716
from functools import partial

from ophyd import ADComponent as ADC
from ophyd import (
    AreaDetector,
    CamBase,
    Component,
    Device,
    EpicsSignal,
    HDF5Plugin,
    OverlayPlugin,
    ProcessPlugin,
    ROIPlugin,
    StatusBase,
)

from dodal.devices.areadetector.plugins.MJPG import SnapshotWithBeamCentre
from dodal.devices.oav.grid_overlay import SnapshotWithGrid
from dodal.devices.oav.oav_parameters import OAVConfigParams


class ZoomController(Device):
    """
    Device to control the zoom level. This should be set like
        o = OAV(name="oav")
        oav.zoom_controller.set("1.0x")

    Note that changing the zoom may change the AD wiring on the associated OAV, as such
    you should wait on any zoom changs to finish before changing the OAV wiring.
    """

    percentage = Component(EpicsSignal, "ZOOMPOSCMD")

    # Level is the string description of the zoom level e.g. "1.0x"
    level = Component(EpicsSignal, "MP:SELECT", string=True)

    zrst = Component(EpicsSignal, "MP:SELECT.ZRST")
    onst = Component(EpicsSignal, "MP:SELECT.ONST")
    twst = Component(EpicsSignal, "MP:SELECT.TWST")
    thst = Component(EpicsSignal, "MP:SELECT.THST")
    frst = Component(EpicsSignal, "MP:SELECT.FRST")
    fvst = Component(EpicsSignal, "MP:SELECT.FVST")
    sxst = Component(EpicsSignal, "MP:SELECT.SXST")

    @property
    def allowed_zoom_levels(self):
        return [
            self.zrst.get(),
            self.onst.get(),
            self.twst.get(),
            self.thst.get(),
            self.frst.get(),
            self.fvst.get(),
            self.sxst.get(),
        ]

    def set(self, level_to_set: str) -> StatusBase:
        return self.level.set(level_to_set)


class OAV(AreaDetector):
    cam = ADC(CamBase, "-DI-OAV-01:CAM:")
    roi = ADC(ROIPlugin, "-DI-OAV-01:ROI:")
    proc = ADC(ProcessPlugin, "-DI-OAV-01:PROC:")
    over = ADC(OverlayPlugin, "-DI-OAV-01:OVER:")
    tiff = ADC(OverlayPlugin, "-DI-OAV-01:TIFF:")
    hdf5 = ADC(HDF5Plugin, "-DI-OAV-01:HDF5:")
    grid_snapshot = Component(SnapshotWithGrid, "-DI-OAV-01:MJPG:")
    snapshot = Component(SnapshotWithBeamCentre, "-DI-OAV-01:MJPG:")
    zoom_controller = Component(ZoomController, "-EA-OAV-01:FZOOM:")

    def __init__(self, *args, params: OAVConfigParams, **kwargs):
        super().__init__(*args, **kwargs)
        self.parameters = params
        self.grid_snapshot.oav_params = params
        self.snapshot.oav_params = params
        self.subscription_id = None
        self._snapshot_trigger_subscription_id = None

    def wait_for_connection(self, all_signals=False, timeout=2):
        connected = super().wait_for_connection(all_signals, timeout)
        x = self.grid_snapshot.x_size.get()
        y = self.grid_snapshot.y_size.get()

        cb = partial(self.parameters.update_on_zoom, xsize=x, ysize=y)

        if self.subscription_id is not None:
            self.zoom_controller.level.unsubscribe(self.subscription_id)
        self.subscription_id = self.zoom_controller.level.subscribe(cb)

        return connected
