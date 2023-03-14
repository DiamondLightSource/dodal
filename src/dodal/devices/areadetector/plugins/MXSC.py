from dodal.devices.oav.grid_overlay import SnapshotWithGrid
from dodal.devices.oav.oav_detector import ZoomController
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


class MXSC(Device):
    """
    Device for edge detection plugin.
    """

    input_plugin_pv: EpicsSignal = Component(EpicsSignal, "NDArrayPort")
    enable_callbacks_pv: EpicsSignal = Component(EpicsSignal, "EnableCallbacks")
    min_callback_time_pv: EpicsSignal = Component(EpicsSignal, "MinCallbackTime")
    blocking_callbacks_pv: EpicsSignal = Component(EpicsSignal, "BlockingCallbacks")
    read_file: EpicsSignal = Component(EpicsSignal, "ReadFile")
    py_filename: EpicsSignal = Component(EpicsSignal, "Filename", string=True)
    preprocess_operation: EpicsSignal = Component(EpicsSignal, "Preprocess")
    preprocess_ksize: EpicsSignal = Component(EpicsSignal, "PpParam1")
    canny_upper_threshold: EpicsSignal = Component(EpicsSignal, "CannyUpper")
    canny_lower_threshold: EpicsSignal = Component(EpicsSignal, "CannyLower")
    close_ksize: EpicsSignal = Component(EpicsSignal, "CloseKsize")
    sample_detection_scan_direction: EpicsSignal = Component(
        EpicsSignal, "ScanDirection"
    )
    sample_detection_min_tip_height: EpicsSignal = Component(
        EpicsSignal, "MinTipHeight"
    )
    tip_x: EpicsSignal = Component(EpicsSignal, "TipX")
    tip_y: EpicsSignal = Component(EpicsSignal, "TipY")
    top: EpicsSignal = Component(EpicsSignal, "Top")
    bottom: EpicsSignal = Component(EpicsSignal, "Bottom")
    output_array: EpicsSignal = Component(EpicsSignal, "OutputArray")
    draw_tip: EpicsSignal = Component(EpicsSignal, "DrawTip")
    draw_edges: EpicsSignal = Component(EpicsSignal, "DrawEdges")
    waveform_size_x: EpicsSignal = Component(EpicsSignal, "ArraySize1_RBV")
    waveform_size_y: EpicsSignal = Component(EpicsSignal, "ArraySize2_RBV")


class OAV(AreaDetector):
    cam: CamBase = ADC(CamBase, "-DI-OAV-01:CAM:")
    roi: ADC = ADC(ROIPlugin, "-DI-OAV-01:ROI:")
    proc: ADC = ADC(ProcessPlugin, "-DI-OAV-01:PROC:")
    over: ADC = ADC(OverlayPlugin, "-DI-OAV-01:OVER:")
    tiff: ADC = ADC(OverlayPlugin, "-DI-OAV-01:TIFF:")
    hdf5: ADC = ADC(HDF5Plugin, "-DI-OAV-01:HDF5:")
    snapshot: SnapshotWithGrid = Component(SnapshotWithGrid, "-DI-OAV-01:MJPG:")
    mxsc: MXSC = ADC(MXSC, "-DI-OAV-01:MXSC:")
    zoom_controller: ZoomController = ADC(ZoomController, "-EA-OAV-01:FZOOM:")
