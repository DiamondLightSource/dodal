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
)

from dodal.devices.areadetector.plugins.MXSC import MXSC
from dodal.devices.oav.grid_overlay import SnapshotWithGrid


class ZoomController(Device):
    """
    Device to control the zoom level, this is unfortunately on a different prefix
    from CAM.
    """

    percentage: EpicsSignal = Component(EpicsSignal, "ZOOMPOSCMD")

    # Level is the arbitrary level  that corresponds to a zoom percentage.
    # When a zoom is fed in from GDA this is the level it is refering to.
    level: EpicsSignal = Component(EpicsSignal, "MP:SELECT")

    zrst: EpicsSignal = Component(EpicsSignal, "MP:SELECT.ZRST")
    onst: EpicsSignal = Component(EpicsSignal, "MP:SELECT.ONST")
    twst: EpicsSignal = Component(EpicsSignal, "MP:SELECT.TWST")
    thst: EpicsSignal = Component(EpicsSignal, "MP:SELECT.THST")
    frst: EpicsSignal = Component(EpicsSignal, "MP:SELECT.FRST")
    fvst: EpicsSignal = Component(EpicsSignal, "MP:SELECT.FVST")

    @property
    def allowed_zoom_levels(self):
        return [
            self.zrst.get(),
            self.onst.get(),
            self.twst.get(),
            self.thst.get(),
            self.frst.get(),
            self.fvst.get(),
        ]


class OAV(AreaDetector):
    cam: CamBase = ADC(CamBase, "CAM:")
    roi: ADC = ADC(ROIPlugin, "ROI:")
    proc: ADC = ADC(ProcessPlugin, "PROC:")
    over: ADC = ADC(OverlayPlugin, "OVER:")
    tiff: ADC = ADC(OverlayPlugin, "TIFF:")
    hdf5: ADC = ADC(HDF5Plugin, "HDF5:")
    snapshot: SnapshotWithGrid = Component(SnapshotWithGrid, "MJPG:")
    mxsc: MXSC = ADC(MXSC, "MXSC:")
    zoom_controller: ZoomController = ADC(ZoomController, "FZOOM:")
