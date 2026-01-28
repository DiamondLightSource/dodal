from ophyd_async.epics.motor import Motor

from dodal.devices.motors import XYZPolarAzimuthStage


class XYZPolarAzimuthDefocusStage(XYZPolarAzimuthStage):
    """
    Six-axis stage with a standard xyz stage and three axis of rotation: polar, azimuth
    and defocus.
    """

    def __init__(self, prefix: str, name=""):
        with self.add_children_as_readables():
            self.defocus = Motor(prefix + "SMDF")
        super().__init__(
            prefix,
            name,
            x_infix="SMX",
            y_infix="SMY",
            z_infix="SMZ",
            polar_infix="POL",
            azimuth_infix="AZM",
        )
