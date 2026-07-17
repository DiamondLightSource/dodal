from typing import Protocol

from pydantic import ConfigDict, StrictFloat, StrictInt
from pydantic.dataclasses import dataclass

from .material_absorption_maths import AbsorptionCalculator
from .transmission_interconversion import attenuation_from_natural_log_of_transmission


@dataclass(kw_only=True, frozen=True, config=ConfigDict(arbitrary_types_allowed=True))
class Absorber:
    material_absorption_model: AbsorptionCalculator

    def _attenuation_bn(self, xray_energy_kev, thickness_cm):
        _alpha = self.material_absorption_model.absorption_coefficient_per_cm(
            energy_kev=xray_energy_kev
        )
        _ln_t = -(thickness_cm * _alpha)
        return attenuation_from_natural_log_of_transmission(_ln_t)


@dataclass(kw_only=True, frozen=True)
class FixedAbsorber(Absorber):
    def calculate_absorption_bn(
        self, xray_energy_kev: StrictInt | StrictFloat
    ) -> float:
        return (
            0.0  # Default to an empty slot, or a wedge OUT, the absorption Bn is zero
        )


class ThicknessProvider(Protocol):
    """Provider API which the standard FoilGeometry implements.

    Used here to make FoilAbsorber easier to test.
    """

    def get_thickness_cm(self) -> float: ...


@dataclass(kw_only=True, frozen=True, config=ConfigDict(arbitrary_types_allowed=True))
class FoilAbsorber(FixedAbsorber):
    geometry_model: ThicknessProvider

    def calculate_absorption_bn(
        self, xray_energy_kev: StrictInt | StrictFloat
    ) -> float:
        _thickness_cm = self.geometry_model.get_thickness_cm()
        return self._attenuation_bn(
            xray_energy_kev=xray_energy_kev, thickness_cm=_thickness_cm
        )


class TaperedGeometryProvider(Protocol):
    """Provider API which the standard WedgeGeometry implements.

    Used here to make WedgeAbsorber easier to test.
    """

    def thickness_cm_at_motor_position_mm(self, motor_position_mm: float) -> float: ...


@dataclass(kw_only=True, frozen=True, config=ConfigDict(arbitrary_types_allowed=True))
class WedgeAbsorber(Absorber):
    geometry_model: TaperedGeometryProvider

    def calculate_absorption_bn(
        self,
        xray_energy_kev: StrictInt | StrictFloat,
        motor_position_mm: StrictInt | StrictFloat,
    ) -> StrictFloat:
        _thickness_cm = self.geometry_model.thickness_cm_at_motor_position_mm(
            motor_position_mm=motor_position_mm
        )
        return self._attenuation_bn(
            xray_energy_kev=xray_energy_kev, thickness_cm=_thickness_cm
        )
