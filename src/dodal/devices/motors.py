from ophyd_async.core import Device
from ophyd_async.epics.motion import Motor


class XYZPositioner(Device):
    """

    Standard ophyd_async xyz motor stage, by combining 3 Motors,
    with added infix for extra flexibliy to allow different axes other than x,y,z.

    Parameters
    ----------
    prefix:
        EPICS PV (Common part up to and including :).
    name:
        name for the stage.
    infix:
        EPICS PV, default is the ["X", "Y", "Z"].
    Notes
    -----
    Example usage::
        async with DeviceCollector():
            xyz_stage = ThreeAxisStage("BLXX-MO-STAGE-XX:")
    Or::
        with DeviceCollector():
            xyz_stage = ThreeAxisStage("BLXX-MO-STAGE-XX:", suffix = [".any",
              ".there", ".motorPv"])

    """

    def __init__(self, prefix: str, name: str, infix: list[str] | None = None):
        if infix is None:
            infix = ["X", "Y", "Z"]
        self.x = Motor(prefix + infix[0])
        self.y = Motor(prefix + infix[1])
        self.z = Motor(prefix + infix[2])
        super().__init__(name=name)
