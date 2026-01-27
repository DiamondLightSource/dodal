from ophyd_async.epics.motor import Motor

from dodal.devices.motors import XYZPolarAzimuthStage


class SampleManipulator(XYZPolarAzimuthStage):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.tilt = Motor(prefix + "TILT")

        super().__init__(prefix=prefix, name=name)
