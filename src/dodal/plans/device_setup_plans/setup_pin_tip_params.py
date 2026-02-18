from functools import partial

import bluesky.plan_stubs as bps

from dodal.devices.oav.oav_parameters import OAVParameters
from dodal.devices.oav.pin_image_recognition import PinTipDetection
from dodal.devices.oav.pin_image_recognition.utils import ScanDirections


def setup_pin_tip_detection_params(
    pin_tip_detect_device: PinTipDetection,
    parameters: OAVParameters,
    scan_direction: ScanDirections = ScanDirections.FORWARD,
    group: str = "pin_tip_parameters",
    wait: bool = True,
):
    set_using_group = partial(bps.abs_set, group=group)
    # select which blur to apply to image
    yield from set_using_group(
        pin_tip_detect_device.preprocess_operation, parameters.preprocess
    )

    # sets length scale for blurring
    yield from set_using_group(
        pin_tip_detect_device.preprocess_ksize, parameters.preprocess_K_size
    )

    # sets iteration for blur
    yield from set_using_group(
        pin_tip_detect_device.preprocess_iterations, parameters.preprocess_iter
    )

    # Canny edge detect - lower
    yield from set_using_group(
        pin_tip_detect_device.canny_lower_threshold,
        parameters.canny_edge_lower_threshold,
    )

    # Canny edge detect - upper
    yield from set_using_group(
        pin_tip_detect_device.canny_upper_threshold,
        parameters.canny_edge_upper_threshold,
    )

    # "Open" morphological operation
    yield from set_using_group(pin_tip_detect_device.open_ksize, parameters.open_ksize)

    # "Close" morphological operation
    yield from set_using_group(
        pin_tip_detect_device.close_ksize, parameters.close_ksize
    )

    # Sample detection direction
    yield from set_using_group(pin_tip_detect_device.scan_direction, scan_direction)

    # Minimum height
    yield from set_using_group(
        pin_tip_detect_device.min_tip_height,
        parameters.minimum_height,
    )

    if wait:
        yield from bps.wait(group=group)
