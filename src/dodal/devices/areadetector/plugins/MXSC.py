from ophyd import Component, Device, EpicsSignal, Kind, Signal
from ophyd.status import Status, SubscriptionStatus


class PinTipDetect(Device):
    INVALID_POSITION = (-1, -1)
    tip_x: EpicsSignal = Component(EpicsSignal, "TipX")
    tip_y: EpicsSignal = Component(EpicsSignal, "TipY")

    triggered_tip: Signal = Component(Signal, kind=Kind.hinted)
    validity_timeout: Signal = Component(Signal, value=1)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update_tip_if_valid(self, value, **_):
        current_value = (value, self.tip_y.get())
        if current_value != self.INVALID_POSITION:
            self.triggered_tip.set(current_value)
            return True

    def trigger(self) -> Status:
        subscription_status = SubscriptionStatus(self.tip_x, self.update_tip_if_valid)

        def set_to_default_and_finish(_):
            self.triggered_tip.set(self.INVALID_POSITION)
            subscription_status.set_finished()

        Status(self, timeout=self.validity_timeout.get()).add_callback(
            set_to_default_and_finish
        )

        return subscription_status


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

    top: EpicsSignal = Component(EpicsSignal, "Top")
    bottom: EpicsSignal = Component(EpicsSignal, "Bottom")
    output_array: EpicsSignal = Component(EpicsSignal, "OutputArray")
    draw_tip: EpicsSignal = Component(EpicsSignal, "DrawTip")
    draw_edges: EpicsSignal = Component(EpicsSignal, "DrawEdges")
    waveform_size_x: EpicsSignal = Component(EpicsSignal, "ArraySize1_RBV")
    waveform_size_y: EpicsSignal = Component(EpicsSignal, "ArraySize2_RBV")

    pin_tip: PinTipDetect = Component(PinTipDetect)
