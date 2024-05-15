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
    Signal,
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
    # Used by OAV to work out if we're changing the setpoint
    _level_sp = Component(Signal)

    zrst = Component(EpicsSignal, "MP:SELECT.ZRST")
    onst = Component(EpicsSignal, "MP:SELECT.ONST")
    twst = Component(EpicsSignal, "MP:SELECT.TWST")
    thst = Component(EpicsSignal, "MP:SELECT.THST")
    frst = Component(EpicsSignal, "MP:SELECT.FRST")
    fvst = Component(EpicsSignal, "MP:SELECT.FVST")
    sxst = Component(EpicsSignal, "MP:SELECT.SXST")

    def set_flatfield_on_zoom_level_one(self, value):
        flat_applied = self.parent.proc.port_name.get()
        no_flat_applied = self.parent.cam.port_name.get()
        return self.parent.grid_snapshot.input_plugin.set(
            flat_applied if value == "1.0x" else no_flat_applied
        )

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
        return_status = self._level_sp.set(level_to_set)
        return_status &= self.level.set(level_to_set)
        return_status &= self.set_flatfield_on_zoom_level_one(level_to_set)
        return return_status


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
        self.add_snapshot_trigger_hook()

    def wait_for_connection(self, all_signals=False, timeout=2):
        connected = super().wait_for_connection(all_signals, timeout)
        x = self.grid_snapshot.x_size.get()
        y = self.grid_snapshot.y_size.get()

        cb = partial(self.parameters.update_on_zoom, xsize=x, ysize=y)

        if self.subscription_id is not None:
            self.zoom_controller.level.unsubscribe(self.subscription_id)
        self.subscription_id = self.zoom_controller.level.subscribe(cb)

        return connected

    def add_snapshot_trigger_hook(self):
        def apply_current_microns_per_pixel_to_snapshot(*args, **kwargs):
            """Persist the current value of the mpp to the snapshot so that it is retained if zoom changes"""
            microns_per_x_pixel = self.parameters.micronsPerXPixel
            microns_per_y_pixel = self.parameters.micronsPerYPixel
            self.grid_snapshot.microns_per_pixel_x.put(microns_per_x_pixel)
            self.grid_snapshot.microns_per_pixel_y.put(microns_per_y_pixel)

        self._snapshot_trigger_subscription_id = (
            self.grid_snapshot.last_saved_path.subscribe(
                apply_current_microns_per_pixel_to_snapshot
            )
        )
