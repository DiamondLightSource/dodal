import bluesky.plan_stubs as bps  # noqa: F401
import bluesky.plans as bp  # noqa: F401

# from bluesky.callbacks.best_effort import BestEffortCallback  # noqa: F401
from bluesky.run_engine import RunEngine, autoawait_in_bluesky_event_loop  # noqa: F401
from ophyd_async.plan_stubs import ensure_connected  # noqa: F401

import dodal.beamlines.i13_1 as bl13j  # noqa: F401
from dodal.plans.i13_1.merlin_test_plans import pcomp_fly_scan  # noqa: F401

#
# --------------------------------
# Motors
kb_y = bl13j.mirror02_vert_y()
theta = bl13j.theta()
pi = bl13j.sample_xyz()
pi_map = bl13j.sample_xyz_map()
pi_map_fa = bl13j.sample_xyz_map_fa()
# --------------------------------
# PMAC and pandas
step25 = bl13j.step_25()
panda01 = bl13j.panda_01()
panda02 = bl13j.panda_02()
# --------------------------------
# Detectors
side_cam = bl13j.side_camera()
merlin = bl13j.merlin()
# --------------------------------
#


# Create a run engine and ensures that await commands happen in the same event loop
# that this uses rather than an ipython specific one.  This avoids some surprising
# behavior that occurs when devices are accessed from multiple event loops.
RE = RunEngine(call_returns_result=True)
# autoawait_in_bluesky_event_loop() # vscode debugger doesn't like this!

# Need matplotlib
# bec = BestEffortCallback()
# RE.subscribe(bec)

RE(
    ensure_connected(
        kb_y, theta, pi, pi_map, pi_map_fa, step25, panda01, panda02, side_cam, merlin
    )
)


# Motor moves:
# RE(bps.rd(kb_y))
# RE(bps.mv(kb_y, 0.6))
# RE(bps.rd(kb_y))


# Generic plans:
# RE(bp.count(detectors=[side_cam], num=2, delay=0.5))
# RE(bp.rel_scan([merlin], kb_y, -0.05, 0.1, 4))
# RE(bp.grid_scan([merlin], pi.y, 10, 13, 4, pi.x, 21, 30, 10, snake_axes=True))


# i13-1 Plans:
# All pi axes are inverted and have to set direction of pcomp so just done theta for now.
# RE(pcomp_fly_scan(m, 0, 10, 11, 1, theta, panda02))
# RE(pcomp_fly_scan(m, 0, 10, 11, 1, pi.y, panda02))
