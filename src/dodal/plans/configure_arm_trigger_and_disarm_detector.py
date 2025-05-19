import time

import bluesky.plan_stubs as bps
from bluesky import preprocessors as bpp
from bluesky.run_engine import RunEngine
from ophyd_async.core import DetectorTrigger
from ophyd_async.fastcs.eiger import EigerDetector, EigerTriggerInfo

from dodal.beamlines.i03 import fastcs_eiger
from dodal.devices.detector import DetectorParams
from dodal.log import LOGGER, do_default_logging_setup


@bpp.run_decorator()
def configure_and_arm_detector(
    eiger: EigerDetector,
    detector_params: DetectorParams,
    trigger_info: EigerTriggerInfo,
):
    assert detector_params.expected_energy_ev
    start = time.time()
    yield from bps.unstage(eiger, wait=True)
    LOGGER.info(f"Stopping Eiger-Odin: {time.time() - start}s")
    start = time.time()
    yield from set_cam_pvs(eiger, detector_params, wait=True)
    LOGGER.info(f"Setting CAM PVs: {time.time() - start}s")
    start = time.time()
    yield from change_roi_mode(eiger, detector_params, wait=True)
    LOGGER.info(f"Changing ROI Mode: {time.time() - start}s")
    start = time.time()
    yield from bps.abs_set(eiger.odin.num_frames_chunks, 1)
    LOGGER.info(f"Setting # of Frame Chunks: {time.time() - start}s")
    start = time.time()
    yield from set_mx_settings_pvs(eiger, detector_params, wait=True)
    LOGGER.info(f"Setting MX PVs: {time.time() - start}s")
    start = time.time()
    yield from bps.prepare(eiger, trigger_info, wait=True)
    LOGGER.info(f"Preparing Eiger: {time.time() - start}s")
    start = time.time()
    yield from bps.kickoff(eiger, wait=True)
    LOGGER.info(f"Kickoff Eiger: {time.time() - start}s")
    start = time.time()
    yield from bps.trigger(eiger.drv.detector.trigger)  # type: ignore
    LOGGER.info(f"Triggering Eiger: {time.time() - start}s")
    start = time.time()
    yield from bps.complete(eiger, wait=True)
    LOGGER.info(f"Completing Capture: {time.time() - start}s")
    start = time.time()
    yield from bps.unstage(eiger, wait=True)
    LOGGER.info(f"Disarming Eiger: {time.time() - start}s")


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

    if wait:
        yield from bps.wait(group)


def change_roi_mode(
    eiger: EigerDetector,
    detector_params: DetectorParams,
    wait: bool,
    group="roi_mode",
):
    detector_dimensions = (
        detector_params.detector_size_constants.roi_size_pixels
        if detector_params.use_roi_mode
        else detector_params.detector_size_constants.det_size_pixels
    )

    yield from bps.abs_set(
        eiger.drv.detector.roi_mode,
        1 if detector_params.use_roi_mode else 0,
        group=group,
    )
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


if __name__ == "__main__":
    RE = RunEngine()
    do_default_logging_setup()
    eiger = fastcs_eiger(connect_immediately=True)
    RE(
        configure_and_arm_detector(
            eiger=eiger,
            detector_params=DetectorParams(
                expected_energy_ev=12800,
                exposure_time_s=0.01,
                directory="/dls/i03/data/2025/cm40607-2/test_new_eiger/",
                prefix="",
                detector_distance=255,
                omega_start=0,
                omega_increment=0.1,
                num_images_per_trigger=1,
                num_triggers=1,
                use_roi_mode=False,
                det_dist_to_beam_converter_path="/dls_sw/i03/software/daq_configuration/lookup/DetDistToBeamXYConverter.txt",
            ),
            trigger_info=EigerTriggerInfo(
                number_of_events=1,
                energy_ev=12800,
                trigger=DetectorTrigger.INTERNAL,
                deadtime=0.0001,
            ),
        )
    )
