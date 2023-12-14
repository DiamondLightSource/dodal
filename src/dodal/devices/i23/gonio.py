from ophyd import Component as Cpt
from ophyd import EpicsMotor
from ophyd.epics_motor import MotorBundle

from dodal.devices.motors import MotorLimitHelper, XYZLimitBundle


class Gonio(MotorBundle):
    x = Cpt(EpicsMotor, "X")
    y = Cpt(EpicsMotor, "Y")
    z = Cpt(EpicsMotor, "Z")
    kappa = Cpt(EpicsMotor, "KAPPA")
    phi = Cpt(EpicsMotor, "PHI")
    omega = Cpt(EpicsMotor, "OMEGA")

    def get_xyz_limits(self) -> XYZLimitBundle:
        """Get the limits for the x, y and z axes.

        Note that these limits may not yet be valid until wait_for_connection is called
        on this MotorBundle.

        Returns:
            XYZLimitBundle: The limits for the underlying motors.
        """
        return XYZLimitBundle(
            MotorLimitHelper(self.x),
            MotorLimitHelper(self.y),
            MotorLimitHelper(self.z),
        )
