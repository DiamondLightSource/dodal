
from typing import Any, Final

from ophyd_async.core import StandardReadable

from dodal.common.general_maths.absorber_geometry import WedgeGeometry
from dodal.common.general_maths.absorbers import VariableDepth
from dodal.devices.beamlines.i19.attenuator_motor_positions import (
    AttenuatorMotorPositions,
    PermittedKeyStr,
)
from dodal.devices.beamlines.i19.transmission.axis_mounted_wedge_logic import (
    AxisMountedWedgeLogic
)
from dodal.devices.beamlines.i19.transmission.retractable_attenuation import (
    LogicalWedge,
)
from dodal.devices.beamlines.i19.transmission.transmission_api import (
    ContinuouslyReadable,
)


class _BaseLogicalWedge(LogicalWedge):

    def __init__(self, *, wedge_identifier: PermittedKeyStr):
        self._identifier = wedge_identifier

    # Unimplemented abstract methods - to be covered in child classes

    async def _read_current_motor_position(self) -> float: ...

    def _predict_attenuation_at_position(self, *, energy_kev:float, position: float) -> float: ...

    def extract_wedge_specific_position_from_motor_positions(
        self, *, motor_positions: AttenuatorMotorPositions
    ) -> float:
        return motor_positions.validated_and_complete[self._identifier]

    def retracted_position(self) -> AttenuatorMotorPositions: ...

    def can_accommodate(
        self, attenuation_demand_bn: float, *, energy_kev: float
    ) -> bool: ...

    def accommodate_demand(
        self,
        attenuation_demand_bn: float,
        *,
        energy_kev: float,
    ) -> AttenuatorMotorPositions:
        """If wedge can accommodate this demand, provide motor position solution.

        Args:
            attenuation_demand_bn:
                Target in logarithmic Barnett attenuation units.
            energy_kev:
                X-ray photon energy in kiloelectronvolts.

        Returns:
            Positional solution for the wedge to meet the demand.

        Raises:
            IneligibleMaterialError if the wedge material is ineligible at this energy.
        """
        ...

    # Implemented async API methods ( defined in Protocol LogicalWedge )

    async def current_motor_position(self) -> AttenuatorMotorPositions:
        latest_position = await self._read_current_motor_position()
        return (
            self._wrap_position_in_attenuator_motor_format(
                a_given_position=latest_position
            )
        )

    def merge_in_retraction_motor_position(self, *, other_motor_positions: AttenuatorMotorPositions | None) -> AttenuatorMotorPositions:
        return self.retracted_position() | other_motor_positions


    def wrap_wedge_axis_position(self, *, axis_position: float | None) -> AttenuatorMotorPositions:
        if axis_position is None:
            return self.retracted_position()
        return self._wrap_position_in_attenuator_motor_format(a_given_position=axis_position)


    def _wrap_position_in_attenuator_motor_format(self, *, a_given_position: float) -> AttenuatorMotorPositions:
        return AttenuatorMotorPositions(
            continuous_positions={self._identifier: a_given_position},
        )


class WedgePositionReadable(ContinuouslyReadable):
    """Wraps Motor converting reads from raw readout to wedge position."""
    def __init__(self, *, readable_axial_motor: StandardReadable):
        self.readable = readable_axial_motor


    @staticmethod
    def _extract_axis_position(raw_readout: dict[str, Any]) -> float:
        signal_data = next(iter(raw_readout.values()))
        return signal_data["value"]


    async def read_continuum_position(self) -> float:
        raw_readout: dict[str, Any] = await self.readable.read()
        return self._extract_axis_position(raw_readout)


class AttenuatingMotorisedWedge(_BaseLogicalWedge):

    def __init__(self,
                 *,
                 wedge_identifier: PermittedKeyStr,
                 absorber: VariableDepth,
                 geometrical_logic: AxisMountedWedgeLogic,
                 axis_readable: ContinuouslyReadable):
        self.readable = axis_readable
        self.absorber = absorber
        self.geometrical_logic = geometrical_logic

        self.retracted_motor_position: Final[AttenuatorMotorPositions] = (
            self._wrap_position_in_attenuator_motor_format(a_given_position=geometry.)
        )
        super().__init__(wedge_identifier=wedge_identifier)


    async def _read_current_motor_position(self) -> float:
        return await self.readable.read_continuum_position()

    def _accommodate_demand(self, *, achieveable_attenuation_demand_bn: float, eligible_energy_kev: float) -> AttenuatorMotorPositions:
        motor_position = (
            self.absorber.calculate_theoretical_motor_position_mm_to_absorb_by(
                absorption_demand_bn=achieveable_attenuation_demand_bn,
                xray_energy_kev=eligible_energy_kev
            )
        )
        return self._wrap_position_in_attenuator_motor_format(
            a_given_position=motor_position
        )

    def _is_a_sub_threshold_demand(self, attenuation_demand_bn: float, *, energy_kev: float) -> bool:
        return (
            attenuation_demand_bn < self._threshold_attenuation_bn(
                energy_kev=energy_kev
            )
        )

    def _predict_attenuation_at_position(self, *, energy_kev:float, position: float) -> float:
        return self.absorber.calculate_absorption_bn(
            xray_energy_kev=energy_kev,
            motor_position_mm=position
        )

    def _threshold_attenuation_bn(self, *, energy_kev: float) -> float:
        wedge_threshold = self.geometrical_logic.threshold_position_mm()
        return self.absorber.calculate_absorption_bn(
            xray_energy_kev=energy_kev,
            motor_position_mm=wedge_threshold
        )

    def retracted_position(self) -> AttenuatorMotorPositions:
        retracted_motor_position = self.geometrical_logic.retracted_position()
        return self._wrap_position_in_attenuator_motor_format(
            a_given_position=retracted_motor_position
        )

    def can_accommodate(
        self, attenuation_demand_bn: float, *, energy_kev: float
    ) -> bool:
        return (
            self.absorber.is_eligible_for_energy(xray_energy_kev=energy_kev)
            and not self._is_a_sub_threshold_demand(
                attenuation_demand_bn=attenuation_demand_bn,
                energy_kev=energy_kev
            )
        )

    def accommodate_demand(
        self,
        attenuation_demand_bn: float,
        *,
        energy_kev: float,
    ) -> AttenuatorMotorPositions:
        """If wedge can accommodate this demand, provide motor position solution.

        Args:
            attenuation_demand_bn:
                Target in logarithmic Barnett attenuation units.
            energy_kev:
                X-ray photon energy in kiloelectronvolts.

        Returns:
            Positional solution for the wedge to meet the demand.

        Raises:
            IneligibleMaterialError if the wedge material is ineligible at this energy.
        """
        return (
            self._accommodate_demand(
                achieveable_attenuation_demand_bn=attenuation_demand_bn,
                eligible_energy_kev=energy_kev
            )
            if self.can_accommodate(
                attenuation_demand_bn=attenuation_demand_bn,
                energy_kev=energy_kev
            )
            else self.retracted_position()
        )
