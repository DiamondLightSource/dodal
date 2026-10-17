import math
from typing import Final, Protocol

from dodal.common.general_maths.absorber_geometry import (
    TaperedGeometryProvider,
    WedgeGeometry,
)
from dodal.common.general_maths.absorbers import VariableDepth, WedgeAbsorber
from dodal.common.general_maths.interval import OpenInterval
from dodal.devices.beamlines.i19.transmission.absorption_contributer import (
    AbsenceFromBeam,
    AbsorptionContributer,
)
from dodal.devices.beamlines.i19.transmission.spec_from_config.lateral_motor_spec import (
    LateralMotorsConfig,
    LateralMotorSpec,
)
from dodal.devices.beamlines.i19.transmission.spec_from_config.material_absorption_spectrum_spec import (
    MaterialAbsorptionSpectralConfig,
    MaterialAbsorptionSpectrum,
)
from dodal.devices.beamlines.i19.transmission.spec_from_config.system_configuration import (
    SystemConfiguration,
)
from dodal.devices.beamlines.i19.transmission.spec_from_config.wedges_spec import (
    WedgesConfig,
    WedgeSpec,
)


class ReadableLinearMotor(Protocol):
    def get_motor_position_mm(self) -> float: ...


class AbsorberWedge(AbsorptionContributer):
    def __init__(
        self,
        *,
        axis_label: str,
        motor_position_reader: ReadableLinearMotor,
        system_config: SystemConfiguration,
    ):
        wedge_spec: WedgeSpec = WedgesConfig.extract_wedge_specifications(
            system_configuration=system_config, wedge_identifier=axis_label
        )
        self.motor_reader: ReadableLinearMotor = motor_position_reader
        self.scale: LateralMotorSpec = (
            LateralMotorsConfig.extract_motors_specifications(
                system_configuration=system_config, motor_identifier=axis_label
            )
        )
        absorber_material_name: str = wedge_spec.material
        absorption_spec = (
            MaterialAbsorptionSpectralConfig.extract_absorber_material_specifications(
                system_configuration=system_config, material_name=absorber_material_name
            )
        )
        absorption_spectrum: MaterialAbsorptionSpectrum = absorption_spec.as_spectrum()
        tapered_geometry: TaperedGeometryProvider = WedgeGeometry(
            taper_cotangent=wedge_spec.geometry.taper_cotangent,
            tip_mm=wedge_spec.geometry.tip,
        )
        self.absorber: Final[VariableDepth] = WedgeAbsorber(
            spectrum=absorption_spectrum,
            geometry_model=tapered_geometry,
        )
        self.id: str = axis_label
        self.voids: list[OpenInterval] = wedge_spec.geometry.voids
        self.absent_when_out = AbsenceFromBeam()

    def _is_out(self, motor_position_mm: float) -> bool:
        return math.isclose(
            motor_position_mm, self.scale.out, abs_tol=self.scale.tolerance
        )

    def _verify_against_voids(self, *, position_to_check_mm: float) -> None:
        for v in self.voids:
            if position_to_check_mm in v:
                _range = f"{v.lower} mm to {v.upper} mm"
                _msg = f"Wedge {self.id} Motor position {position_to_check_mm} mm found within forbidden range {_range}."
                raise ValueError(_msg)
        return None

    def calculate_absorption_bn(
        self,
        *,
        xray_energy_kev: float,
        motor_position_mm: float,
    ) -> float:
        if self._is_out(motor_position_mm=motor_position_mm):
            return self.absent_when_out.predict_absorption_at_given_energy(
                xray_energy_kev=xray_energy_kev
            )
        self._verify_against_voids(position_to_check_mm=motor_position_mm)
        return self.absorber.calculate_absorption_bn(
            xray_energy_kev=xray_energy_kev, motor_position_mm=motor_position_mm
        )

    def is_feasible(self, *, xray_energy_kev: float, demand_bn: float) -> bool:
        return self.is_suitable_for_energy(
            xray_energy_kev=xray_energy_kev
        ) and not self._threshold_absorption_exceeds_demand(
            xray_energy_kev=xray_energy_kev, demand_bn=demand_bn
        )

    def _threshold_absorption_exceeds_demand(
        self, *, xray_energy_kev: float, demand_bn: float
    ) -> bool:
        min_absorption = self.calculate_absorption_bn(
            xray_energy_kev=xray_energy_kev, motor_position_mm=self.scale.threshold
        )
        return min_absorption > demand_bn

    def predict_absorption_at_given_energy(self, *, xray_energy_kev: float) -> float:
        motor_position = self.motor_reader.get_motor_position_mm()
        return self.calculate_absorption_bn(
            xray_energy_kev=xray_energy_kev, motor_position_mm=motor_position
        )
