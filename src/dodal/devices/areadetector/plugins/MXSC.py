from typing import List, Tuple

import numpy as np
from ophyd import Component, Device, EpicsSignal, EpicsSignalRO, Kind, Signal
from ophyd.status import StableSubscriptionStatus, Status, StatusBase

from dodal.log import LOGGER

Pixel = Tuple[int, int]


def statistics_of_positions(
    positions: List[Pixel],
) -> Tuple[Pixel, Tuple[float, float]]:
    """Get the median and standard deviation from a list of readings.

    Note that x/y are treated separately so the median position is not guaranteed to be
    a position that was actually read.

    Args:
        positions (List[Pixel]): A list of tip positions.

    Returns:
        Tuple[Pixel, Tuple[float, float]]: The median tip position and the standard
                                           deviation in x/y
    """
    x_coords, y_coords = np.array(positions).T

    median = (int(np.median(x_coords)), int(np.median(y_coords)))
    std = (np.std(x_coords, dtype=float), np.std(y_coords, dtype=float))

    return median, std


class PinTipDetect(Device):
    """This will read the pin tip location from the MXSC plugin.

    If the plugin finds no tip it will return {INVALID_POSITION}. However, it will also
    occassionally give incorrect data. Therefore, it is recommended that you trigger
    this device, which will set {triggered_tip} to a median of the valid points taken
    for {settle_time_s} seconds.

    If no valid points are found within {validity_timeout} seconds a {triggered_tip}
    will be set to {INVALID_POSITION}.
    """

    INVALID_POSITION = (-1, -1)
    tip_x = Component(EpicsSignalRO, "TipX")
    tip_y = Component(EpicsSignalRO, "TipY")

    triggered_tip = Component(Signal, kind=Kind.hinted, value=INVALID_POSITION)
    validity_timeout = Component(Signal, value=5)
    settle_time_s = Component(Signal, value=0.5)

    def log_tips_and_statistics(self, _):
        median, standard_deviation = statistics_of_positions(self.tip_positions)
        LOGGER.info(
            f"Found tips {self.tip_positions} with median {median} and standard deviation {standard_deviation}"
        )

    def update_tip_if_valid(self, value: int, **_):
        current_value = (value, int(self.tip_y.get()))
        if current_value != self.INVALID_POSITION:
            self.tip_positions.append(current_value)

            (
                median_tip_location,
                __,
            ) = statistics_of_positions(self.tip_positions)

            self.triggered_tip.put(median_tip_location)
            return True
        return False

    def trigger(self) -> StatusBase:
        self.tip_positions: List[Pixel] = []

        subscription_status = StableSubscriptionStatus(
            self.tip_x,
            self.update_tip_if_valid,
            stability_time=self.settle_time_s.get(),
            run=True,
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
        subscription_status.add_callback(self.log_tips_and_statistics)

        return subscription_status


class MXSC(Device):
    """
    Device for edge detection plugin.
    """

    input_plugin = Component(EpicsSignal, "NDArrayPort")
    enable_callbacks = Component(EpicsSignal, "EnableCallbacks")
    min_callback_time = Component(EpicsSignal, "MinCallbackTime")
    blocking_callbacks = Component(EpicsSignal, "BlockingCallbacks")
    read_file = Component(EpicsSignal, "ReadFile")
    filename = Component(EpicsSignal, "Filename", string=True)
    preprocess_operation = Component(EpicsSignal, "Preprocess")
    preprocess_ksize = Component(EpicsSignal, "PpParam1")
    canny_upper_threshold = Component(EpicsSignal, "CannyUpper")
    canny_lower_threshold = Component(EpicsSignal, "CannyLower")
    close_ksize = Component(EpicsSignal, "CloseKsize")
    sample_detection_scan_direction = Component(EpicsSignal, "ScanDirection")
    sample_detection_min_tip_height = Component(EpicsSignal, "MinTipHeight")

    top = Component(EpicsSignal, "Top")
    bottom = Component(EpicsSignal, "Bottom")
    output_array = Component(EpicsSignal, "OutputArray")
    draw_tip = Component(EpicsSignal, "DrawTip")
    draw_edges = Component(EpicsSignal, "DrawEdges")
    waveform_size_x = Component(EpicsSignal, "ArraySize1_RBV")
    waveform_size_y = Component(EpicsSignal, "ArraySize2_RBV")

    pin_tip = Component(PinTipDetect, "")
