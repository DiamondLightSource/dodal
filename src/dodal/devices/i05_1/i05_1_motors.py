from ophyd_async.epics.motor import Motor

from dodal.devices.motors import XYZPolarAzimuthStage


class XYZPolarAzimuthDefocusStage(XYZPolarAzimuthStage):
    """
    Six-axis stage with a standard xyz stage and three axis of rotation: polar, azimuth
    and defocus.
    """

    def __init__(
        self,
        prefix: str,
        x_infix="SMX",
        y_infix="SMY",
        z_infix="SMZ",
        polar_infix="POL",
        azimuth_infix="AZM",
        defocus_infix="SDMF",
        name="",
    ):
        with self.add_children_as_readables():
            self.defocus = Motor(prefix + defocus_infix)
        super().__init__(
            prefix,
            name,
            x_infix=x_infix,
            y_infix=y_infix,
            z_infix=z_infix,
            polar_infix=polar_infix,
            azimuth_infix=azimuth_infix,
        )
