import bluesky.plan_stubs as bps
from ophyd_async.epics.eiger import EigerDetector

from dodal.devices.detector import DetectorParams


def load_metadata(
    eiger: EigerDetector, energy: float, enable: bool, detector_params: DetectorParams
):
    yield from change_roi_mode(eiger, enable, detector_params)
    yield from bps.abs_set(eiger.drv.photon_energy, energy)
    yield from bps.abs_set(eiger.odin.num_frames_chunks, 1)
    yield from set_mx_settings_pvs(eiger, detector_params, wait=True)


def change_roi_mode(
    eiger: EigerDetector, enable: bool, detector_params: DetectorParams
):
    detector_dimensions = (
        detector_params.detector_size_constants.roi_size_pixels
        if enable
        else detector_params.detector_size_constants.det_size_pixels
    )

    yield from bps.abs_set(eiger.drv.roi_mode, 1 if enable else 0)
    yield from bps.abs_set(eiger.odin.image_height, detector_dimensions.height)
    yield from bps.abs_set(eiger.odin.image_width, detector_dimensions.width)
    yield from bps.abs_set(eiger.odin.num_row_chunks, detector_dimensions.height)
    yield from bps.abs_set(eiger.odin.num_col_chunks, detector_dimensions.width)


def set_mx_settings_pvs(
    eiger: EigerDetector,
    detector_params: DetectorParams,
    wait: bool,
    group="mx_settings",
):
    beam_x_pixels, beam_y_pixels = detector_params.get_beam_position_pixels(
        detector_params.detector_distance
    )

    yield from bps.abs_set(eiger.drv.beam_centre_x, beam_x_pixels, group)
    yield from bps.abs_set(eiger.drv.beam_centre_y, beam_y_pixels, group)
    yield from bps.abs_set(
        eiger.drv.det_distance, detector_params.detector_distance, group
    )

    yield from bps.abs_set(eiger.drv.omega_start, detector_params.omega_start, group)
    yield from bps.abs_set(
        eiger.drv.omega_increment, detector_params.omega_increment, group
    )

    if wait:
        yield from bps.wait(group)
