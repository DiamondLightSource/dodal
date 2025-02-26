import time

import bluesky.plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.epics.eiger import EigerDetector, EigerTriggerInfo

from dodal.beamlines.i03 import fastcs_eiger
from dodal.devices.detector import DetectorParams
from dodal.log import LOGGER, do_default_logging_setup

params = DetectorParams(
    expected_energy_ev=12700,
    exposure_time=0.004,
    directory="/dls/i03/data/2025/cm40607-2/test_new_eiger",
    prefix="",
    detector_distance=255,
    omega_start=0,
    omega_increment=0.2,
    num_images_per_trigger=1,
    num_triggers=50,
    use_roi_mode=True,
    det_dist_to_beam_converter_path="/dls_sw/i03/software/daq_configuration/lookup/DetDistToBeamXYConverter.txt",
)


def load_metadata(
    eiger: EigerDetector,
    enable: bool,
    detector_params: DetectorParams,
):
    start = time.time()
    assert detector_params.expected_energy_ev
    yield from bps.abs_set(eiger.odin.file_writer.capture, 0)  # type: ignore
    yield from bps.abs_set(eiger.odin.meta.stop_writing, 1)  # type: ignore
    LOGGER.info(f"Stopping Odin: {time.time() - start}s")
    yield from set_cam_pvs(eiger, detector_params, wait=True)
    LOGGER.info(f"Setting CAM PVs: {time.time() - start}s")
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
    LOGGER.info(f"Preparing Eiger: {time.time() - start}s")


def set_cam_pvs(
    eiger: EigerDetector,
    detector_params: DetectorParams,
    wait: bool,
    group="cam_pvs",
):
    yield from bps.abs_set(
        eiger.drv.acquire_time, detector_params.exposure_time, group=group
    )
    yield from bps.abs_set(
        eiger.drv.acquire_period, detector_params.exposure_time, group=group
    )
    yield from bps.abs_set(eiger.drv.num_exposures, 1, group=group)
    yield from bps.abs_set(eiger.drv.trigger_mode, "exts", group=group)
    # Image mode not set...

    if wait:
        yield from bps.wait(group)


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
    do_default_logging_setup()
    eiger = fastcs_eiger(connect_immediately=True)
    RE(load_metadata(eiger=eiger, enable=True, detector_params=params))
