from ophyd import Component, Device, EpicsSignal, EpicsSignalRO, Kind, Signal
from ophyd.status import Status, SubscriptionStatus


class PinTipDetect(Device):
    """This will read the pin tip location from the MXSC plugin.

    If the plugin finds no tip it will return {INVALID_POSITION}. However, it will also
    occassionally give false negatives and return this value when there is a pin tip
    there. Therefore, it is recommended that you trigger this device, which will cause a
    subsequent read to return a valid pin immediatedly if one is found or wait
    {validity_timeout} seconds if one is not, at which point a subsequent read will give
    you {INVALID_POSITION}.
    """

    INVALID_POSITION = (-1, -1)
    tip_x: EpicsSignalRO = Component(EpicsSignalRO, "TipX")
    tip_y: EpicsSignalRO = Component(EpicsSignalRO, "TipY")

    triggered_tip: Signal = Component(Signal, kind=Kind.hinted, value=INVALID_POSITION)
    validity_timeout: Signal = Component(Signal, value=5)

    def update_tip_if_valid(self, value, **_):
        current_value = (value, self.tip_y.get())
        if current_value != self.INVALID_POSITION:
            self.triggered_tip.put(current_value)
            return True

    def trigger(self) -> Status:
        subscription_status = SubscriptionStatus(
            self.tip_x, self.update_tip_if_valid, run=True
        )

        def set_to_default_and_finish(timeout_status: Status):
            try:
                if not timeout_status.success:
                    self.triggered_tip.set(self.INVALID_POSITION)
                    subscription_status.set_finished()
            except Exception as e:
                subscription_status.set_exception(e)

        # We use a separate status for measuring the timeout as we don't want an error
        # on the returned status
        self._timeout_status = Status(self, timeout=self.validity_timeout.get())
        self._timeout_status.add_callback(set_to_default_and_finish)
        subscription_status.add_callback(lambda _: self._timeout_status.set_finished())

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

    pin_tip: PinTipDetect = Component(PinTipDetect, "")
