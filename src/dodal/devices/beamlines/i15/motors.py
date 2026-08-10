from ophyd_async.epics.motor import Motor

from dodal.devices.motors import Stage


class UpstreamDownstreamPair(Stage):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.upstream = Motor(prefix + "US")
            self.downstream = Motor(prefix + "DS")
        super().__init__(name=name)


class NumberedTripleAxisStage(Stage):
    def __init__(
        self,
        prefix: str,
        name: str = "",
        axis1_infix: str = "AXIS1",
        axis2_infix: str = "AXIS2",
        axis3_infix: str = "AXIS3",
    ):
        with self.add_children_as_readables():
            self.axis1 = Motor(prefix + axis1_infix)
            self.axis2 = Motor(prefix + axis2_infix)
            self.axis3 = Motor(prefix + axis3_infix)
        super().__init__(name=name)
