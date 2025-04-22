import time

import bluesky.plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.core import DetectorTrigger
from ophyd_async.fastcs.eiger import EigerDetector, EigerTriggerInfo

from dodal.beamlines.i03 import fastcs_eiger
from dodal.devices.detector import DetectorParams
from dodal.log import LOGGER, do_default_logging_setup

params = DetectorParams(
    expected_energy_ev=12800,
    exposure_time_s=0.01,
    directory="/scratch/rye74444/test_eiger",
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
    yield from bps.abs_set(eiger.odin.capture, 0)
    LOGGER.info(f"Stopping Odin: {time.time() - start}s")
    yield from set_cam_pvs(eiger, detector_params, wait=True)
    LOGGER.info(f"Setting CAM PVs: {time.time() - start}s")
    yield from set_odin_pvs(eiger, detector_params, wait=True)
    LOGGER.info(f"Setting Odin PVs: {time.time() - start}s")
    yield from change_roi_mode(eiger, enable, detector_params, wait=True)
    LOGGER.info(f"Changing ROI Mode: {time.time() - start}s")
    yield from bps.abs_set(eiger.odin.num_frames_chunks, 1)
    LOGGER.info(f"Setting # of Frame Chunks: {time.time() - start}s")
    yield from set_mx_settings_pvs(eiger, detector_params, wait=True)
    LOGGER.info(f"Setting MX PVs: {time.time() - start}s")

    trigger_info = EigerTriggerInfo(
        number_of_events=detector_params.num_triggers,
        energy_ev=detector_params.expected_energy_ev,
        trigger=DetectorTrigger.INTERNAL,
        deadtime=0.0001,
    )

    yield from bps.prepare(eiger, trigger_info, wait=True)
    LOGGER.info(f"Preparing Eiger: {time.time() - start}s")


def set_cam_pvs(
    eiger: EigerDetector,
    detector_params: DetectorParams,
    wait: bool,
    group="cam_pvs",
):
    yield from bps.abs_set(
        eiger.drv.detector.count_time, detector_params.exposure_time_s, group=group
    )
    yield from bps.abs_set(
        eiger.drv.detector.frame_time, detector_params.exposure_time_s, group=group
    )
    yield from bps.abs_set(eiger.drv.detector.nexpi, 1, group=group)
    yield from bps.abs_set(eiger.drv.detector.trigger_mode, "ints", group=group)
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

    yield from bps.abs_set(eiger.drv.detector.roi_mode, 1 if enable else 0, group=group)
    yield from bps.abs_set(
        eiger.odin.image_height,
        detector_dimensions.height,
        group=group,
    )
    yield from bps.abs_set(
        eiger.odin.image_width,
        detector_dimensions.width,
        group=group,
    )
    yield from bps.abs_set(
        eiger.odin.num_row_chunks,
        detector_dimensions.height,
        group=group,
    )
    yield from bps.abs_set(
        eiger.odin.num_col_chunks,
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

    yield from bps.abs_set(eiger.drv.detector.beam_center_x, beam_x_pixels, group)
    yield from bps.abs_set(eiger.drv.detector.beam_center_y, beam_y_pixels, group)
    yield from bps.abs_set(
        eiger.drv.detector.detector_distance, detector_params.detector_distance, group
    )

    yield from bps.abs_set(
        eiger.drv.detector.omega_start, detector_params.omega_start, group
    )
    yield from bps.abs_set(
        eiger.drv.detector.omega_increment, detector_params.omega_increment, group
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
        eiger.odin.file_path,
        detector_params.directory,
        group=group,
    )
    yield from bps.abs_set(
        eiger.odin.file_name,
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
