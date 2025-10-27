from math import ceil

import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
from bluesky.utils import MsgGenerator
from ophyd_async.core import DetectorTrigger, FlyMotorInfo, StandardFlyer, TriggerInfo

# from ophyd_async.epics.adaravis import AravisDetector
from ophyd_async.epics.motor import Motor
from ophyd_async.fastcs.panda import (
    HDFPanda,
    PandaPcompDirection,
    PcompInfo,
    StaticPcompTriggerLogic,
)

from dodal.devices.i13_1.merlin import Merlin
from dodal.plan_stubs.data_session import attach_data_session_metadata_decorator

# for calculations
MRES_PI = 2.16600375e-7
OFF_Y = 113.3
MRES_THETA = 0.0001
OFF_THETA = 0


def pcomp_fly_scan(
    detector: Merlin,
    # detector: AravisDetector,
    start: int,
    stop: int,
    num: int,
    duration: float,
    motor: Motor,
    panda: HDFPanda,
) -> MsgGenerator:
    """
    Perform a fly scan.

    Args:
        start (float): Starting position in mm.
        stop (float): Ending position in mm.
        num (int): Number of steps.
        duration (float): Duration to acquire each frame, in seconds.
        motor (Motor): Motor instance.
        panda (HDFPanda): Data acquisition device.

    Yields:
    - Messages for the scan process (MsgGenerator).
    """

    # Describes the Panda PCOMP block.
    # It is responsible for generating the triggers based on a position and step size.
    panda_pcomp = StandardFlyer(StaticPcompTriggerLogic(panda.pcomp[1]))

    # MRES changes depending on the motor.
    # Getting this value from the motor will be soon available through an async function
    if motor.name == "sample_xyz-y":
        mres = MRES_PI
        off = OFF_Y
    elif motor.name == "theta":
        mres = MRES_THETA
        off = OFF_THETA
    else:
        raise ValueError(f"Motor name ({motor.name}) not supported")

    @attach_data_session_metadata_decorator()
    @bpp.run_decorator()
    @bpp.stage_decorator([panda, panda_pcomp])
    def inner_plan():
        width = (stop - start) / (num - 1)
        start_pos = start - (width / 2)
        stop_pos = stop + (width / 2)
        motor_info = FlyMotorInfo(
            start_position=start_pos,
            end_position=stop_pos,
            time_for_move=num * duration,
        )
        # Info used to generate the triggers.
        panda_pcomp_info = PcompInfo(
            start_postion=ceil(start_pos / mres + off),
            pulse_width=10,
            rising_edge_step=ceil(width / mres + off),
            number_of_pulses=num,
            direction=PandaPcompDirection.POSITIVE,
        )

        # Info on configuring the data writer block for the Panda device.
        # This sets the number of frames that are expected.
        panda_hdf_info = TriggerInfo(
            number_of_events=num,
            trigger=DetectorTrigger.CONSTANT_GATE,
            livetime=duration,
            deadtime=1e-5,
        )

        detector_info = TriggerInfo(
            number_of_events=num,
            trigger=DetectorTrigger.CONSTANT_GATE,
            livetime=duration - 1e-3,
            deadtime=1e-3,
        )

        # The order of these prepare calls does not matter, as we are setting the PVs.
        yield from bps.prepare(motor, motor_info)
        yield from bps.prepare(panda, panda_hdf_info)
        yield from bps.prepare(detector, detector_info)
        yield from bps.prepare(panda_pcomp, panda_pcomp_info, wait=True)

        # Kickoff the motor last to ensure other components are initialized first.
        # Otherwise, the motor might move before other devices are ready.
        yield from bps.kickoff(panda)
        yield from bps.kickoff(panda_pcomp, wait=True)
        yield from bps.kickoff(detector, wait=True)
        yield from bps.kickoff(motor, wait=True)

        # Needs to wait for each flyable object to complete.
        yield from bps.complete_all(motor, panda_pcomp, panda, detector, wait=True)
        yield from bps.complete_all(motor, detector, wait=True)

    yield from inner_plan()
