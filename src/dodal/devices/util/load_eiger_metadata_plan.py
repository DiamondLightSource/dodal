import time

import bluesky.plan_stubs as bps
from bluesky.run_engine import RunEngine
from mx_bluesky.common.utils.log import LOGGER
from ophyd_async.epics.eiger import EigerDetector, EigerTriggerInfo

from dodal.devices.detector import DetectorParams


def load_metadata(
    eiger: EigerDetector,
    enable: bool,
    detector_params: DetectorParams,
):
    start = time.time()
    assert detector_params.expected_energy_ev
    yield from bps.stage(eiger)
    LOGGER.info(f"Staging Eiger: {time.time() - start}s")
    yield from set_odin_pvs(eiger, detector_params, wait=True)
    LOGGER.info(f"Setting Odin PVs: {time.time() - start}s")
    yield from change_roi_mode(eiger, enable, detector_params, wait=True)
    LOGGER.info(f"Changing ROI Mode: {time.time() - start}s")
    yield from bps.abs_set(eiger.odin.file_writer.num_frames_chunks, 1)  # type: ignore
    LOGGER.info(f"Setting # of Frame Chunks: {time.time() - start}s")
    yield from set_mx_settings_pvs(eiger, detector_params, wait=True)
    LOGGER.info(f"Setting MX PVs: {time.time() - start}s")

    trigger_info = EigerTriggerInfo(
        number_of_triggers=detector_params.num_triggers,
        energy_ev=detector_params.expected_energy_ev,
    )

    yield from bps.prepare(eiger, trigger_info)


def change_roi_mode(
    eiger: EigerDetector,
    enable: bool,
    detector_params: DetectorParams,
    wait: bool,
    group="roi_mode",
):
    detector_dimensions = (
        detector_params.detector_size_constants.roi_size_pixels
        if enable
        else detector_params.detector_size_constants.det_size_pixels
    )

    yield from bps.abs_set(eiger.drv.roi_mode, 1 if enable else 0, group=group)
    yield from bps.abs_set(
        eiger.odin.file_writer.image_height,  # type: ignore
        detector_dimensions.height,
        group=group,
    )
    yield from bps.abs_set(
        eiger.odin.file_writer.image_width,  # type: ignore
        detector_dimensions.width,
        group=group,
    )
    yield from bps.abs_set(
        eiger.odin.file_writer.num_row_chunks,  # type: ignore
        detector_dimensions.height,
        group=group,
    )
    yield from bps.abs_set(
        eiger.odin.file_writer.num_col_chunks,  # type: ignore
        detector_dimensions.width,
        group=group,
    )

    if wait:
        yield from bps.wait(group)


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
    eiger: EigerDetector,
    detector_params: DetectorParams,
    wait: bool,
    group="odin_pvs",
):
    yield from bps.abs_set(
        eiger.odin.file_writer.file_path,  # type: ignore
        detector_params.directory,
        group=group,
    )
    yield from bps.abs_set(
        eiger.odin.file_writer.file_name,  # type: ignore
        detector_params.full_filename,
        group=group,
    )

    if wait:
        yield from bps.wait(group)


if __name__ == "__main__":
    RE = RunEngine()
