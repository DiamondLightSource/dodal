from typing import Annotated, Protocol, runtime_checkable

from pydantic import ConfigDict, Field, StrictFloat, validate_call
from pydantic.dataclasses import dataclass

from dodal.common.general_maths.absorber_geometry import (
    TaperedGeometryProvider,
    ThicknessProvider,
)
from dodal.common.general_maths.material_absorption_maths import AbsorptionCalculator
from dodal.common.general_maths.transmission_interconversion import (
    attenuation_from_natural_log_of_transmission,
)

XrayEnergy = Annotated[
    StrictFloat,
    Field(gt=0.1, le=30.0, description="X-rays from 0.1 keV to 30.0"),
]


@runtime_checkable
class FixedDepth(Protocol):
    def calculate_absorption_bn(self, xray_energy_kev: XrayEnergy) -> float:
        """Calculates absorption for a flat absorber of fixed depth.

        Typical use case is a foil absorber in a filter wheel.

        Args:
            xray_energy_kev: The energy of the x-ray photons in kiloelectonvolts.

        Returns:
            Absorption in the logarithmic Barnett units (Bn).
            N.B. logarithmic absorption units are used for system attenuation budget calculations.
        """
        ...


@runtime_checkable
class VariableDepth(Protocol):
    def calculate_absorption_bn(
        self,
        xray_energy_kev: XrayEnergy,
        motor_position_mm: StrictFloat,
    ) -> float:
        """Calculates absorption for an absorber of variable depth.

        Typical use case is a wedge absorber mounted on a lateral axis motor.

        Args:
            xray_energy_kev: The energy of the x-ray photons (kiloelectronvolts).
            motor_position_mm: The wedge position as defined in motor coordinates (mm).

        Returns:
            Absorption in the logarithmic Barnett units (Bn).
            N.B. logarithmic absorption units are used for system attenuation budget calculations.
        """
        ...


@dataclass(kw_only=True, frozen=True, config=ConfigDict(arbitrary_types_allowed=True))
class Absorber:
    """Base class for individual attenuating absorber.

    This is a system level entity in the business logic of a transmission subsystem,
    combines geometry and material absorption models, to yield attenuation calculations.
    N.B. natural units are cm for depth of absorber and logarithmic absorption units.

    Attributes:
        material_absorption_model: Material specific model for photon mass attenuation calculation.
    """

    material_absorption_model: AbsorptionCalculator

    def _attenuation_bn(self, xray_energy_kev, thickness_cm):
        """Common internal conversion calculator.

        Extracts material photon mass attenuation from material calculator,
        and with the input thickness, derives the logarithmic attenuation.

        Args:
            xray_energy_kev: Energy of x-ray photons (kiloelectronvolts).
            thickness_cm: Material depth of the absorber (cm).

        Returns:
            Attenuation in 'system budget friendly' logarithmic units (Barnett units, Bn).
        """
        _alpha = self.material_absorption_model.absorption_coefficient_per_cm(
            energy_kev=xray_energy_kev
        )
        _ln_t = -(thickness_cm * _alpha)
        return attenuation_from_natural_log_of_transmission(_ln_t)


@dataclass(kw_only=True, frozen=True, config=ConfigDict(arbitrary_types_allowed=True))
class FoilAbsorber(Absorber, FixedDepth):
    """System level representation of an foil absorbing filter, typically wheel mounted.

    Attributes:
        geometry_model: Shape model implementing the ThicknessProvider protocol.

    Returns:
            Attenuation in 'system budget friendly' logarithmic units (Barnett units, Bn).
    """

    geometry_model: ThicknessProvider

    @validate_call
    def calculate_absorption_bn(self, xray_energy_kev: XrayEnergy) -> float:
        # see Protocol API for FixedDepth (absorber)
        _thickness_cm = self.geometry_model.get_thickness_cm()
        return self._attenuation_bn(
            xray_energy_kev=xray_energy_kev, thickness_cm=_thickness_cm
        )


@dataclass(kw_only=True, frozen=True, config=ConfigDict(arbitrary_types_allowed=True))
class WedgeAbsorber(Absorber, VariableDepth):
    """System level representation of an foil absorbing filter, typically wheel mounted.

    Attributes:
        geometry_model: Shape model implementing the TaperedGeometryProvider protocol.

    Returns:
        Attenuation in 'system budget friendly' logarithmic units (Barnett units, Bn).
    """

    geometry_model: TaperedGeometryProvider

    @validate_call
    def calculate_absorption_bn(
        self,
        xray_energy_kev: XrayEnergy,
        motor_position_mm: StrictFloat,
    ) -> float:
        # see Protocol API for VariableDepth (absorber)
        _thickness_cm = self.geometry_model.thickness_cm_at_motor_position_mm(
            motor_position_mm=motor_position_mm
        )
        return self._attenuation_bn(
            xray_energy_kev=xray_energy_kev, thickness_cm=_thickness_cm
        )
