from enum import Enum

from ophyd import Component as Cpt
from ophyd import Device, EpicsMotor, EpicsSignal
from ophyd.epics_motor import MotorBundle
from ophyd.status import StatusBase

from dodal.devices.motors import MotorLimitHelper, XYZLimitBundle
from dodal.devices.status import await_approx_value
from dodal.devices.util.epics_util import SetWhenEnabled
from dodal.devices.util.motor_utils import ExtendedEpicsMotor


class StubPosition(Enum):
    CURRENT_AS_CENTER = 0
    RESET_TO_ROBOT_LOAD = 1


class StubOffsets(Device):
    """Stub offsets are used to change the internal co-ordinate system of the smargon by
    adding an offset to x, y, z.
    This is useful as the smargon's centre of rotation is around (0, 0, 0). As such
    changing stub offsets will change the centre of rotation.
    In practice we don't need to change them manually, instead there are helper PVs to
    set them so that the current position is zero or to pre-defined positions.
    """

    parent: "Smargon"

    center_at_current_position = Cpt(SetWhenEnabled, "CENTER_CS")
    to_robot_load = Cpt(SetWhenEnabled, "SET_STUBS_TO_RL")

    def set(self, pos: StubPosition) -> StatusBase:
        if pos == StubPosition.CURRENT_AS_CENTER:
            status = self.center_at_current_position.set(1)
            status &= await_approx_value(self.parent.x, 0.0, deadband=0.1)
            status &= await_approx_value(self.parent.y, 0.0, deadband=0.1)
            status &= await_approx_value(self.parent.z, 0.0, deadband=0.1)
            return status
        else:
            return self.to_robot_load.set(1)


class Smargon(MotorBundle):
    """
    Real motors added to allow stops following pin load (e.g. real_x1.stop() )
    X1 and X2 real motors provide compound chi motion as well as the compound X travel,
    increasing the gap between x1 and x2 changes chi, moving together changes virtual x.
    Robot loading can nudge these and lead to errors.
    """

    x = Cpt(ExtendedEpicsMotor, "X")
    y = Cpt(EpicsMotor, "Y")
    z = Cpt(EpicsMotor, "Z")
    chi = Cpt(EpicsMotor, "CHI")
    phi = Cpt(EpicsMotor, "PHI")
    omega = Cpt(ExtendedEpicsMotor, "OMEGA")

    real_x1 = Cpt(EpicsMotor, "MOTOR_3")
    real_x2 = Cpt(EpicsMotor, "MOTOR_4")
    real_y = Cpt(EpicsMotor, "MOTOR_1")
    real_z = Cpt(EpicsMotor, "MOTOR_2")
    real_phi = Cpt(EpicsMotor, "MOTOR_5")
    real_chi = Cpt(EpicsMotor, "MOTOR_6")

    stub_offsets = Cpt(StubOffsets, "")

    disabled = Cpt(EpicsSignal, "DISABLED")

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
