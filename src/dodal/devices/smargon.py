from enum import Enum
from functools import partial

from ophyd import Component as Cpt
from ophyd import Device, EpicsMotor, EpicsSignalRO
from ophyd.epics_motor import MotorBundle
from ophyd.status import Status, StatusBase

from dodal.devices.motors import MotorLimitHelper, XYZLimitBundle
from dodal.devices.status import await_approx_value
from dodal.devices.utils import SetWhenEnabled, run_functions_without_blocking


class StubPosition(Enum):
    CURRENT_AS_CENTER = 0
    RESET_TO_ROBOT_LOAD = 1


class StubApplied(Enum):
    NOT_APPLIED = 0
    APPLIED = 1


class StubOffsets(Device):
    """Stub offsets are used to change the internal co-ordinate system of the smargon by
    adding an offset to x, y, z.
    This is useful as the smargon's centre of rotation is around (0, 0, 0). As such
    changing stub offsets will change the centre of rotation.
    In practice we don't need to change them manually, instead there are helper PVs to
    set them so that the current position is zero or to pre-defined positions.
    """

    parent: "Smargon"

    stub_applied: EpicsSignalRO = Cpt(EpicsSignalRO, "NEW_CS_CENTER")

    center_at_current_position: SetWhenEnabled = Cpt(SetWhenEnabled, "CENTER_CS")
    to_robot_load: SetWhenEnabled = Cpt(SetWhenEnabled, "SET_STUBS_TO_RL")

    def _center_to_current(self) -> StatusBase:
        status = self.center_at_current_position.set(1)
        status &= await_approx_value(self.parent.x, 0.0, deadband=0.1)
        status &= await_approx_value(self.parent.y, 0.0, deadband=0.1)
        status &= await_approx_value(self.parent.z, 0.0, deadband=0.1)
        return status

    def set(self, pos: StubPosition) -> StatusBase:
        """Sets stub offsets to either current position as center or to robot load
        position.

        If current position is already the center it will first reset to robot load.
        If robot load position is requested and we are already there then do nothing.
        """
        if pos == StubPosition.CURRENT_AS_CENTER:
            if self.stub_applied.get() == StubApplied.APPLIED.value:
                reset_position = [
                    partial(self.to_robot_load.set, 1),
                    self._center_to_current,
                ]
                return run_functions_without_blocking(reset_position)
            else:
                return self._center_to_current()
        else:
            if self.stub_applied.get() == StubApplied.APPLIED.value:
                return self.to_robot_load.set(1)
            else:
                do_nothing_status = Status()
                do_nothing_status.set_finished()
                return do_nothing_status


class Smargon(MotorBundle):
    """
    Real motors added to allow stops following pin load (e.g. real_x1.stop() )
    X1 and X2 real motors provide compound chi motion as well as the compound X travel,
    increasing the gap between x1 and x2 changes chi, moving together changes virtual x.
    Robot loading can nudge these and lead to errors.
    """

    x: EpicsMotor = Cpt(EpicsMotor, "X")
    y: EpicsMotor = Cpt(EpicsMotor, "Y")
    z: EpicsMotor = Cpt(EpicsMotor, "Z")
    chi: EpicsMotor = Cpt(EpicsMotor, "CHI")
    phi: EpicsMotor = Cpt(EpicsMotor, "PHI")
    omega: EpicsMotor = Cpt(EpicsMotor, "OMEGA")

    real_x1: EpicsMotor = Cpt(EpicsMotor, "MOTOR_3")
    real_x2: EpicsMotor = Cpt(EpicsMotor, "MOTOR_4")
    real_y: EpicsMotor = Cpt(EpicsMotor, "MOTOR_1")
    real_z: EpicsMotor = Cpt(EpicsMotor, "MOTOR_2")
    real_phi: EpicsMotor = Cpt(EpicsMotor, "MOTOR_5")
    real_chi: EpicsMotor = Cpt(EpicsMotor, "MOTOR_6")

    stub_offsets: StubOffsets = Cpt(StubOffsets, "")

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
