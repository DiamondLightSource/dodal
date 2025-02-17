import bluesky.plan_stubs as bps
from ophyd_async.epics.eiger import EigerDetector, EigerTriggerInfo

from dodal.devices.detector import DetectorParams


def load_metadata(
    eiger: EigerDetector,
    enable: bool,
    detector_params: DetectorParams,
):
    assert detector_params.expected_energy_ev
    yield from set_odin_pvs(eiger, detector_params, wait=True)
    yield from change_roi_mode(eiger, enable, detector_params)
    yield from bps.abs_set(eiger.odin.num_frames_chunks, 1)
    yield from set_mx_settings_pvs(eiger, detector_params, wait=True)

    trigger_info = EigerTriggerInfo(
        number_of_triggers=detector_params.num_triggers,
        energy_ev=detector_params.expected_energy_ev,
    )

    yield from bps.prepare(eiger, trigger_info)


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


def set_odin_pvs(
    eiger: EigerDetector, detector_params: DetectorParams, wait: bool, group="odin_pvs"
):
    yield from bps.abs_set(eiger.odin.file_path, detector_params.directory, group=group)
    yield from bps.abs_set(
        eiger.odin.file_name, detector_params.full_filename, group=group
    )
