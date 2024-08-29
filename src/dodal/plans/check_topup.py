from typing import Any

import bluesky.plan_stubs as bps

from dodal.common.beamlines.beamline_parameters import (
    get_beamline_parameters,
)
from dodal.devices.synchrotron import Synchrotron, SynchrotronMode
from dodal.log import LOGGER

ALLOWED_MODES = [SynchrotronMode.USER, SynchrotronMode.SPECIAL]
DECAY_MODE_COUNTDOWN = -1  # Value of the start_countdown PV when in decay mode
COUNTDOWN_DURING_TOPUP = 0

DEFAULT_THRESHOLD_EXPOSURE_S = 120
DEFAULT_TOPUP_GATE_DELAY_S = 1


class TopupConfig:
    # For planned exposures less than this value, wait for topup to finish instead of
    # collecting throughout topup.
    THRESHOLD_EXPOSURE_S = "dodal_topup_threshold_exposure_s"
    # Additional configurable safety margin to wait after the end of topup, as the start
    # and end countdowns do not have the same precision, and in addition we want to be sure
    # that collection does not overlap with any transients that may occur after the
    # nominal endpoint.
    TOPUP_GATE_DELAY_S = "dodal_topup_end_delay_s"


def _in_decay_mode(time_to_topup):
    if time_to_topup == DECAY_MODE_COUNTDOWN:
        LOGGER.info("Machine in decay mode, gating disabled")
        return True
    return False


def _gating_permitted(machine_mode: SynchrotronMode):
    if machine_mode in ALLOWED_MODES:
        LOGGER.info("Machine in allowed mode, gating top up enabled.")
        return True
    LOGGER.info("Machine not in allowed mode, gating disabled")
    return False


def _delay_to_avoid_topup(
    total_run_time_s: float,
    time_to_topup_s: float,
    topup_configuration: dict,
    total_exposure_time_s: float,
) -> bool:
    """Determine whether we should delay collection until after a topup. Generally
    if a topup is due to occur during the collection we will delay collection until after the topup.
    However for long-running collections, impact of the topup is potentially less and collection-duration may be
    a significant fraction of the topup-interval, therefore we may wish to collect during a topup.

    Args:
        total_run_time_s: Anticipated time until end of the collection in seconds
        time_to_topup_s: Time to the start of the topup as measured from the PV
        topup_configuration: configuration dictionary
        total_exposure_time_s: Total exposure time of the sample in s"""
    if total_run_time_s > time_to_topup_s:
        limit_s = topup_configuration.get(
            TopupConfig.THRESHOLD_EXPOSURE_S, DEFAULT_THRESHOLD_EXPOSURE_S
        )
        gate = total_exposure_time_s < limit_s
        if gate:
            LOGGER.info(f"""
                Exposure time of {total_exposure_time_s}s below the threshold of {limit_s}s.
                Collection delayed until topup done.
                """)
        else:
            LOGGER.info(f"""
                Exposure time of {total_exposure_time_s}s meets the threshold of {limit_s}s.
                Collection proceeding through topup.
                """)
        return gate
    LOGGER.info(
        """
        Total run time less than time to next topup. Proceeding with collection.
        """
    )
    return False


def wait_for_topup_complete(synchrotron: Synchrotron):
    LOGGER.info("Waiting for topup to complete")
    start = yield from bps.rd(synchrotron.top_up_start_countdown)
    while start == COUNTDOWN_DURING_TOPUP:
        yield from bps.sleep(0.1)
        start = yield from bps.rd(synchrotron.top_up_start_countdown)


def check_topup_and_wait_if_necessary(
    synchrotron: Synchrotron,
    total_exposure_time: float,
    ops_time: float,  # Account for xray centering, rotation speed, etc
):  # See https://github.com/DiamondLightSource/hyperion/issues/932
    """A small plan to check if topup gating is permitted and sleep until the topup\
        is over if it starts before the end of collection.

    Args:
        synchrotron (Synchrotron): Synchrotron device.
        total_exposure_time (float): Expected total exposure time for \
            collection, in seconds.
        ops_time (float): Additional time to account for various operations,\
            eg. x-ray centering, in seconds. Defaults to 30.0.
    """
    machine_mode = yield from bps.rd(synchrotron.synchrotron_mode)
    assert isinstance(machine_mode, SynchrotronMode)
    time_to_topup = yield from bps.rd(synchrotron.top_up_start_countdown)
    if _in_decay_mode(time_to_topup) or not _gating_permitted(machine_mode):
        yield from bps.null()
        return
    tot_run_time = total_exposure_time + ops_time
    end_topup = yield from bps.rd(synchrotron.top_up_end_countdown)
    topup_configuration = _load_topup_configuration_from_properties_file()
    should_wait = _delay_to_avoid_topup(
        tot_run_time,
        time_to_topup,
        topup_configuration,
        total_exposure_time,
    )
    topup_gate_delay = topup_configuration.get(
        TopupConfig.TOPUP_GATE_DELAY_S, DEFAULT_TOPUP_GATE_DELAY_S
    )
    time_to_wait = end_topup + topup_gate_delay if should_wait else 0.0

    yield from bps.sleep(time_to_wait)

    check_start = yield from bps.rd(synchrotron.top_up_start_countdown)
    if check_start == COUNTDOWN_DURING_TOPUP:
        yield from wait_for_topup_complete(synchrotron)


def _load_topup_configuration_from_properties_file() -> dict[str, Any]:
    params = get_beamline_parameters()
    return params.params
