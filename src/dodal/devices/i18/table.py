from ophyd_async.epics.motor import Motor

from dodal.devices.motors import XYZStage


class Table(XYZStage):
    def __init__(self, prefix: str, name: str = "") -> None:
        with self.add_children_as_readables():
            self.theta = Motor(prefix + "THETA")
        super().__init__(prefix, name)
