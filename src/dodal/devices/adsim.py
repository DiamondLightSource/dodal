from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor


class SimStage(StandardReadable):
    """Simulated Sample Stage for use with the containerised simulated beamline
    https://github.com/epics-containers/example-services"""

    def __init__(self, prefix: str, name: str = "sim"):
        with self.add_children_as_readables():
            self.x = Motor(prefix + "M1")
            self.y = Motor(prefix + "M2")
        super().__init__(name=name)
