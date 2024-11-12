from ophyd_async.core import StandardReadable
from ophyd_async.epics.core import epics_signal_r
from ophyd_async.epics.motor import Motor


class CTAB(StandardReadable):
    """Basic collimantion table (CTAB) device for motion plus the motion disable signal
    when laser curtain triggered and hutch not locked.

    CTAB has 3 physical vertical motors, the jacks. 1 upstream and 2 downstream.
    The two downstream jacks are labelled as outboard (away from the ring) and
    inboard (towards the ring).
    Together these 3 jacks provide compound motion for vertical motion and pitch/roll.
    There are 2 physical horizontal motors 1 upstream, 1 downstream. These provide yaw.

    CTAB motion is disabled by an object being within the laser curtain area and can be
    overriden by use of the dead man's handle device or locking the hutch. The effect of
    these disabling systems is to cut power to the motors - signal for this is crate_power
    """

    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.inboard_y = Motor(prefix + "-MO-TABLE-01:INBOARDY")
            self.outboard_y = Motor(prefix + "-MO-TABLE-01:OUTBOARDY")
            self.upstream_y = Motor(prefix + "-MO-TABLE-01:UPSTREAMY")
            self.combined_downstream_y = Motor(prefix + "-MO-TABLE-01:DOWNSTREAMY")
            self.combined_all_y = Motor(prefix + "-MO-TABLE-01:Y")

            self.downstream_x = Motor(prefix + "-MO-TABLE-01:DOWNSTREAMX")
            self.upstream_x = Motor(prefix + "-MO-TABLE-01:UPSTREAMX")
            self.combined_all_x = Motor(prefix + "-MO-TABLE-01:X")

            self.pitch = Motor(prefix + "-MO-TABLE-01:PITCH")
            self.roll = Motor(prefix + "-MO-TABLE-01:ROLL")
            self.yaw = Motor(prefix + "-MO-TABLE-01:YAW")

            self.crate_power = epics_signal_r(
                int, prefix + "-MO-PMAC-02:CRATE2_HEALTHY"
            )  # returns 0 if no power

            super().__init__(name)
