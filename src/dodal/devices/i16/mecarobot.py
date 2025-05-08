import asyncio

from bluesky.protocols import Locatable, Location
from ophyd_async.core import (
    DerivedSignalFactory,
    DeviceVector,
    StandardReadable,
    Transform,
    soft_signal_rw,
    wait_for_value,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

from dodal.devices.i16.kinematics_solutions import (
    CartesianSpace,
    JointSpace,
    forward_kinematics,
    inverse_kinematics,
)


class RobotTransform(Transform):
    """Transform raw joints values to derived axes, and vice versa."""

    def raw_to_derived(
        self,
        *,
        joint_1: float,
        joint_2: float,
        joint_3: float,
        joint_4: float,
        joint_5: float,
        joint_6: float,
    ) -> CartesianSpace:
        """Transform joints angles to cartesian x, y, z, alpha, beta, and gamma."""
        cartesian_pose = forward_kinematics(
            [joint_1, joint_2, joint_3, joint_4, joint_5, joint_6], 70, "xyz"
        )
        return cartesian_pose

    def derived_to_raw(
        self,
        *,
        x: float,
        y: float,
        z: float,
        alpha: float,
        beta: float,
        gamma: float,
        joint_1: float,
        joint_2: float,
        joint_3: float,
        joint_4: float,
        joint_5: float,
        joint_6: float,
    ) -> JointSpace:
        """Transform cartesian x, y, z, alpha, beta, and gamma to joint angles."""
        try:
            derived_readings = inverse_kinematics(
                [x, y, z],
                [alpha, beta, gamma],
                [joint_1, joint_2, joint_3, joint_4, joint_5, joint_6],
            )
        except RuntimeWarning as err:
            raise ValueError(
                "Invalid tool-tip pose:"
                f"x={x}, y={y}, z={z}, alpha={alpha}, beta={beta}, gamma={gamma}."
                "Failed to generate joint space pose."
            ) from err

        return derived_readings


class Meca500(StandardReadable, Locatable[CartesianSpace]):
    """Meca500 device that derives x, y, z, alpha, beta, and gamma, from joints."""

    def __init__(self, prefix="", name="") -> None:
        with self.add_children_as_readables():
            self.joints = DeviceVector(
                {
                    i: epics_signal_rw(
                        float, f"{prefix}JOINTS:THETA{i + 1}:SP", name=f"joint_{i + 1}"
                    )
                    for i in range(0, 6)
                }
            )

        self.move_joints_array = epics_signal_rw(
            int, f"{prefix}PREPARE_MOVE_JOINTS_ARRAY.PROC"
        )
        self.busy = epics_signal_rw(str, f"{prefix}ROBOT:STATUS:BUSY")
        self.eom = epics_signal_r(float, f"{prefix}ROBOT:STATUS:EOM")

        self._factory = DerivedSignalFactory(
            RobotTransform,
            self.set,
            joint_1=self.joints[0],
            joint_2=self.joints[1],
            joint_3=self.joints[2],
            joint_4=self.joints[3],
            joint_5=self.joints[4],
            joint_6=self.joints[5],
        )

        self.x = self._factory.derived_signal_rw(float, "x")
        self.y = self._factory.derived_signal_rw(float, "y")
        self.z = self._factory.derived_signal_rw(float, "z")
        self.alpha = self._factory.derived_signal_rw(float, "alpha")
        self.beta = self._factory.derived_signal_rw(float, "beta")
        self.gamma = self._factory.derived_signal_rw(float, "gamma")

        self.x_sp = soft_signal_rw(float, name="x")
        self.y_sp = soft_signal_rw(float, name="y")
        self.z_sp = soft_signal_rw(float, name="z")
        self.alpha_sp = soft_signal_rw(float, name="alpha")
        self.beta_sp = soft_signal_rw(float, name="beta")
        self.gamma_sp = soft_signal_rw(float, name="gamma")

        super().__init__(name=name)

    async def set(self, target_cartesian: CartesianSpace) -> None:  # type: ignore  # noqa: D102
        """Set cartesian position of manipulator."""
        transform = await self._factory.transform()

        await asyncio.gather(
            self.x_sp.set(target_cartesian["x"]),
            self.y_sp.set(target_cartesian["y"]),
            self.z_sp.set(target_cartesian["z"]),
            self.alpha_sp.set(target_cartesian["alpha"]),
            self.beta_sp.set(target_cartesian["beta"]),
            self.gamma_sp.set(target_cartesian["gamma"]),
        )

        values = await asyncio.gather(
            *(self.joints[i].get_value() for i in range(len(self.joints)))
        )

        current_joint_positions = JointSpace(
            **{f"joint_{i + 1}": value for i, value in enumerate(values)}
        )

        raw = transform.derived_to_raw(**target_cartesian, **current_joint_positions)

        self.busy.set("BUSY", wait=True)
        await asyncio.gather(
            *(
                self.joints[i].set(raw[self.joints[i].name])
                for i in range(len(self.joints))
            )
        )
        await self.move_joints_array.set(True)
        await wait_for_value(self.eom, 0.0, timeout=5)

    async def locate(self) -> Location[CartesianSpace]:
        """Return last commanded and current cartesian position of tooltip."""
        virtual_setpoints = CartesianSpace(
            x=await self.x_sp.get_value(),
            y=await self.y_sp.get_value(),
            z=await self.z_sp.get_value(),
            alpha=await self.alpha_sp.get_value(),
            beta=await self.beta_sp.get_value(),
            gamma=await self.gamma_sp.get_value(),
        )

        virtual_readbacks = CartesianSpace(
            x=await self.x.get_value(),
            y=await self.y.get_value(),
            z=await self.z.get_value(),
            alpha=await self.alpha.get_value(),
            beta=await self.beta.get_value(),
            gamma=await self.gamma.get_value(),
        )

        return Location(setpoint=virtual_setpoints, readback=virtual_readbacks)
