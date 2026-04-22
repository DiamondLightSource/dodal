from ophyd_async.epics.motor import Motor

from dodal.devices.motors import _PHI, _X, _Y, XYPhiStage


class PEEMManipulator(XYPhiStage):
    """Three-axis stage with a standard xy stage and one axis of rotation: phi. This
    also has an additional energy slit (es) motor.
    """

    def __init__(
        self,
        prefix: str,
        x_infix: str = _X,
        y_infix: str = _Y,
        phi_infix: str = _PHI,
        es_infix: str = "ES:TRANS",
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            self.es = Motor(prefix + es_infix)
        super().__init__(prefix, x_infix, y_infix, phi_infix, name)
