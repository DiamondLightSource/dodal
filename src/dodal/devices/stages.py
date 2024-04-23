from ophyd_async.core import Device
from ophyd_async.epics.motion.motor import Motor

from dodal.devices.epics.setReadOnlyMotor import SetReadOnlyMotor


class ThreeAxisStage(Device):
    """

    Standard ophyd_async xyz motor stage, by combining 3 Motors.

    Parameters
    ----------
    prefix:
        EPICS PV (None common part up to and including :).
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


class SingleBasicStage(Device):
    """

    Standard ophyd_async basic single stage, This stage contain only value and readback
    (no stop). This is quite common for example single piezo driver on mirrors.

    Parameters
    ----------
    prefix:
        EPICS PV (None common part up to and including :).
    name:
        name for the stage.
    suffix:
        EPICS PV, default is the [".VAL", ".RBV", "EGU"].
        Mostly use for correct non-standard pv
    Notes
    -----
    Example usage::
        async with DeviceCollector():
            piezo1 = SingleBasicStage("BLXX-MO-STAGE-XX:")
    Or::
        with DeviceCollector():
            piezo1 = SingleBasicStage("BLXX-MO-STAGE-XX:", suffix = [".stupid",
              ".non-standard", ".Pv"])

    """

    def __init__(self, prefix: str, name: str, suffix: list[str] | None = None):
        if suffix is None:
            suffix = [".VAL", ".RBV", ".EGU"]
        self.stage = SetReadOnlyMotor(prefix, name, suffix)
        super().__init__(name=name)
