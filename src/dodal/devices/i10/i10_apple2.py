from typing import SupportsFloat

import numpy as np
from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    Reference,
    StandardReadable,
    StandardReadableFormat,
    derived_signal_rw,
    soft_signal_rw,
)

from dodal.devices.insertion_device.apple2_undulator import (
    MAXIMUM_MOVE_TIME,
    Apple2,
    Apple2Controller,
    Apple2PhasesVal,
    Apple2Val,
    Pol,
    UndulatorGap,
    UndulatorJawPhase,
    UndulatorPhaseAxes,
)
from dodal.devices.insertion_device.energy_motor_lookup import EnergyMotorLookup

ROW_PHASE_MOTOR_TOLERANCE = 0.004
MAXIMUM_ROW_PHASE_MOTOR_POSITION = 24.0
MAXIMUM_GAP_MOTOR_POSITION = 100
DEFAULT_JAW_PHASE_POLY_PARAMS = [1.0 / 7.5, -120.0 / 7.5]
ALPHA_OFFSET = 180


class I10Apple2(Apple2[UndulatorPhaseAxes]):
    """I10Apple2 device is an apple2 with extra jaw phase motor."""

    def __init__(
        self,
        id_gap: UndulatorGap,
        id_phase: UndulatorPhaseAxes,
        id_jaw_phase: UndulatorJawPhase,
        name: str = "",
    ) -> None:
        """
        Parameters:
        ------------
        id_gap : UndulatorJawPhase
            The gap motor of the undulator.
        id_phase : UndulatorJawPhase
            The phase motors of the undulator.
        id_jaw_phase : UndulatorJawPhase
            The jaw phase motor of the undulator.
        name : str, optional
            The name of the device, by default "".
        """
        with self.add_children_as_readables():
            self.jaw_phase = Reference(id_jaw_phase)
        super().__init__(id_gap=id_gap, id_phase=id_phase, name=name)


class I10Apple2Controller(Apple2Controller[I10Apple2]):
    """
    I10Apple2Controller is a extension of Apple2Controller which provide linear
    arbitrary angle control.
    """

    def __init__(
        self,
        apple2: I10Apple2,
        gap_energy_motor_lut: EnergyMotorLookup,
        phase_energy_motor_lut: EnergyMotorLookup,
        jaw_phase_limit: float = 12.0,
        jaw_phase_poly_param: list[float] = DEFAULT_JAW_PHASE_POLY_PARAMS,
        angle_threshold_deg=30.0,
        units: str = "eV",
        name: str = "",
    ) -> None:
        """
        Parameters:
        -----------
        apple2 : I10Apple2
            An I10Apple2 device.
        gap_energy_motor_lut: EnergyMotorLookup
            The class that handles the gap look up table logic for the insertion device.
        phase_energy_motor_lut: EnergyMotorLookup
            The class that handles the phase look up table logic for the insertion device.
        jaw_phase_limit : float, optional
            The maximum allowed jaw_phase movement., by default 12.0
        jaw_phase_poly_param : list[float], optional
            polynomial parameters highest power first., by default DEFAULT_JAW_PHASE_POLY_PARAMS
        angle_threshold_deg : float, optional
            The angle threshold to switch between 0-180 and 180-360 range., by default 30.0
        units:
            the units of this device. Defaults to eV.
        name : str, optional
            New device name.
        """
        self.gap_energy_motor_lut = gap_energy_motor_lut
        self.phase_energy_motor_lut = phase_energy_motor_lut
        super().__init__(
            apple2=apple2,
            gap_energy_motor_converter=gap_energy_motor_lut.find_value_in_lookup_table,
            phase_energy_motor_converter=phase_energy_motor_lut.find_value_in_lookup_table,
            units=units,
            name=name,
        )
        self.jaw_phase_from_angle = np.poly1d(jaw_phase_poly_param)
        self.angle_threshold_deg = angle_threshold_deg
        self.jaw_phase_limit = jaw_phase_limit
        self._linear_arbitrary_angle = soft_signal_rw(float, initial_value=None)

        self.linear_arbitrary_angle = derived_signal_rw(
            raw_to_derived=self._read_linear_arbitrary_angle,
            set_derived=self._set_linear_arbitrary_angle,
            pol_angle=self._linear_arbitrary_angle,
            pol=self.polarisation,
        )

    def _read_linear_arbitrary_angle(self, pol_angle: float, pol: Pol) -> float:
        self._raise_if_not_la(pol)
        return pol_angle

    async def _set_linear_arbitrary_angle(self, pol_angle: float) -> None:
        pol = await self.polarisation.get_value()
        self._raise_if_not_la(pol)
        # Moving to real angle which is 210 to 30.
        alpha_real = (
            pol_angle
            if pol_angle > self.angle_threshold_deg
            else pol_angle + ALPHA_OFFSET
        )
        jaw_phase = self.jaw_phase_from_angle(alpha_real)
        if abs(jaw_phase) > self.jaw_phase_limit:
            raise RuntimeError(
                f"jaw_phase position for angle ({pol_angle}) is outside permitted range"
                f" [-{self.jaw_phase_limit}, {self.jaw_phase_limit}]"
            )
        await self.apple2().jaw_phase().set(jaw_phase)
        await self._linear_arbitrary_angle.set(pol_angle)

    def _get_apple2_value(self, gap: float, phase: float, pol: Pol) -> Apple2Val:
        phase3 = phase * (-1 if pol == Pol.LA else 1)
        return Apple2Val(
            gap=f"{gap:.6f}",
            phase=Apple2PhasesVal(
                top_outer=f"{phase:.6f}",
                top_inner="0.0",
                btm_inner=f"{phase3:.6f}",
                btm_outer="0.0",
            ),
        )

    async def _set_motors_from_energy_and_polarisation(
        self, energy: float, pol: Pol
    ) -> None:
        await super()._set_motors_from_energy_and_polarisation(energy, pol)
        if pol != Pol.LA:
            await self.apple2().jaw_phase().set(0)
            await self.apple2().jaw_phase().set_move.set(1)

    def _raise_if_not_la(self, pol: Pol) -> None:
        if pol != Pol.LA:
            raise RuntimeError(
                "Angle control is not available in polarisation"
                + f" {pol} with {self.name}"
            )


class LinearArbitraryAngle(StandardReadable, Movable[SupportsFloat]):
    """
    Device to set the polarisation angle of the Apple2 undulator in Linear Arbitrary (LA) mode.
    """

    def __init__(
        self,
        id_controller: I10Apple2Controller,
        name: str = "",
    ) -> None:
        """
        Parameters
        ----------
        id_controller : I10Apple2Controller
            The I10Apple2Controller which control the ID.
        name : str, optional
            New device name.
        """
        super().__init__(name=name)
        self.linear_arbitrary_angle = Reference(id_controller.linear_arbitrary_angle)

        self.add_readables(
            [self.linear_arbitrary_angle()],
            StandardReadableFormat.HINTED_SIGNAL,
        )

    @AsyncStatus.wrap
    async def set(self, angle: float) -> None:
        await self.linear_arbitrary_angle().set(angle, timeout=MAXIMUM_MOVE_TIME)
