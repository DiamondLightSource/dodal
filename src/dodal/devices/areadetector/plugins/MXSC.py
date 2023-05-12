from ophyd import Component, Device, EpicsSignal


class MXSC(Device):
    """
    Device for edge detection plugin.
    """

    input_plugin: EpicsSignal = Component(EpicsSignal, "NDArrayPort")
    enable_callbacks: EpicsSignal = Component(EpicsSignal, "EnableCallbacks")
    min_callback_time: EpicsSignal = Component(EpicsSignal, "MinCallbackTime")
    blocking_callbacks: EpicsSignal = Component(EpicsSignal, "BlockingCallbacks")
    read_file: EpicsSignal = Component(EpicsSignal, "ReadFile")
    filename: EpicsSignal = Component(EpicsSignal, "Filename", string=True)
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
