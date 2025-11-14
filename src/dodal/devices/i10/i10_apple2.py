from typing import SupportsFloat

import numpy as np
from bluesky.protocols import Movable
from daq_config_server.client import ConfigServer
from ophyd_async.core import (
    AsyncStatus,
    Reference,
    StandardReadable,
    StandardReadableFormat,
    derived_signal_rw,
    soft_signal_rw,
)

from dodal.devices.apple2_undulator import (
    Apple2,
    Apple2Controller,
    Apple2PhasesVal,
    Apple2Val,
    Pol,
    UndulatorGap,
    UndulatorJawPhase,
    UndulatorPhaseAxes,
)
from dodal.devices.util.lookup_tables_apple2 import (
    BaseEnergyMotorLookup,
    LookupTableConfig,
    convert_csv_to_lookup,
)
from dodal.log import LOGGER

ROW_PHASE_MOTOR_TOLERANCE = 0.004
MAXIMUM_ROW_PHASE_MOTOR_POSITION = 24.0
MAXIMUM_GAP_MOTOR_POSITION = 100
DEFAULT_JAW_PHASE_POLY_PARAMS = [1.0 / 7.5, -120.0 / 7.5]
ALPHA_OFFSET = 180
MAXIMUM_MOVE_TIME = 550  # There is no useful movements take longer than this.


class I10EnergyMotorLookup(BaseEnergyMotorLookup):
    """
    Handles lookup tables for I10 Apple2 ID, converting energy and polarisation to gap
     and phase. Fetches and parses lookup tables from a config server, supports dynamic
     updates, and validates input.
    """

    def update_lookuptable(self):
        """
        Update lookup tables from files and validate their format.
        """
        LOGGER.info("Updating lookup dictionary from file for gap.")
        gap_csv_file = self.config_client.get_file_contents(
            self.lut_config.path.gap, reset_cached_result=True
        )
        self.lookup_tables.gap = convert_csv_to_lookup(
            file_contents=gap_csv_file, lut_config=self.lut_config
        )
        self.available_pol = list(self.lookup_tables.gap.root.keys())

        LOGGER.info("Updating lookup dictionary from file for phase.")
        phase_csv_file = self.config_client.get_file_contents(
            self.lut_config.path.phase, reset_cached_result=True
        )
        self.lookup_tables.phase = convert_csv_to_lookup(
            file_contents=phase_csv_file, lut_config=self.lut_config
        )


class I10Apple2(Apple2):
    def __init__(
        self,
        id_gap: UndulatorGap,
        id_phase: UndulatorPhaseAxes,
        id_jaw_phase: UndulatorJawPhase,
        name: str = "",
    ) -> None:
        """
        I10Apple2 device is an apple2 with extra jaw phase motor.

        Parameters
        ----------

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
        config_client: ConfigServer,
        lut_config: LookupTableConfig,
        jaw_phase_limit: float = 12.0,
        jaw_phase_poly_param: list[float] = DEFAULT_JAW_PHASE_POLY_PARAMS,
        angle_threshold_deg=30.0,
        name: str = "",
    ) -> None:
        """

        parameters
        ----------
        apple2 : I10Apple2
            An I10Apple2 device.
        lookuptable_dir : str
            The path to look up table.
        source : tuple[str, str]
            The column name and the name of the source in look up table. e.g. ( "source", "idu")
        config_client : ConfigServer
            The config server client to fetch the look up table.
        jaw_phase_limit : float, optional
            The maximum allowed jaw_phase movement., by default 12.0
        jaw_phase_poly_param : list[float], optional
            polynomial parameters highest power first., by default DEFAULT_JAW_PHASE_POLY_PARAMS
        angle_threshold_deg : float, optional
            The angle threshold to switch between 0-180 and 180-360 range., by default 30.0
        name : str, optional
            New device name.
        """

        self.lookup_table_client = I10EnergyMotorLookup(
            lut_config=lut_config,
            config_client=config_client,
        )
        super().__init__(
            apple2=apple2,
            energy_to_motor_converter=self.lookup_table_client.get_motor_from_energy,
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

    async def _set_motors_from_energy(self, value: float) -> None:
        """
        Set the undulator motors for a given energy and polarisation.
        """

        pol = await self._check_and_get_pol_setpoint()
        gap, phase = self.energy_to_motor(energy=value, pol=pol)
        phase3 = phase * (-1 if pol == Pol.LA else 1)
        id_set_val = Apple2Val(
            gap=f"{gap:.6f}",
            phase=Apple2PhasesVal(
                top_outer=f"{phase:.6f}",
                top_inner="0.0",
                btm_inner=f"{phase3:.6f}",
                btm_outer="0.0",
            ),
        )

        LOGGER.info(f"Setting polarisation to {pol}, with values: {id_set_val}")
        await self.apple2().set(id_motor_values=id_set_val)
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
        await self.linear_arbitrary_angle().set(angle)
