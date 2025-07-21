from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor


class CollimationTable(StandardReadable):
    """Basic collimation table device for motion plus the motion disable signal
    when laser curtain triggered and hutch not locked.

    The table has 3 physical vertical motors, the jacks. 1 upstream and 2 downstream.
    The two downstream jacks are labelled as outboard (away from the ring) and
    inboard (towards the ring).
    Together these 3 jacks provide compound motion for vertical motion and pitch/roll.
    There are 2 physical horizontal motors 1 upstream, 1 downstream. These provide yaw.

    Table motion is disabled by an object being within the laser curtain area and can be
    overridden by use of the dead man's handle device or locking the hutch. The effect of
    these disabling systems is to cut power to the motors - signal for this is crate_power
    """

    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.inboard_y = Motor(f"{prefix}:INBOARDY")
            self.outboard_y = Motor(f"{prefix}:OUTBOARDY")
            self.upstream_y = Motor(f"{prefix}:UPSTREAMY")
            self.combined_downstream_y = Motor(f"{prefix}:DOWNSTREAMY")
            self.combined_all_y = Motor(f"{prefix}:Y")

            self.downstream_x = Motor(f"{prefix}:DOWNSTREAMX")
            self.upstream_x = Motor(f"{prefix}:UPSTREAMX")
            self.combined_all_x = Motor(f"{prefix}:X")

            self.pitch = Motor(f"{prefix}:PITCH")
            self.roll = Motor(f"{prefix}:ROLL")
            self.yaw = Motor(f"{prefix}:YAW")

            super().__init__(name)
