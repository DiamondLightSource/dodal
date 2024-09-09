from ophyd_async.core import StandardReadable
from ophyd_async.epics.motor import Motor


class TrainingRigSampleStage(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.x = Motor(prefix + "X")
            self.theta = Motor(prefix + "A")
        super().__init__(name)
