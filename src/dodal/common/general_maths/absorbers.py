from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, StrictFloat, validate_call

from dodal.common.general_maths.absorber_geometry import (
    TaperedGeometryProvider,
    ThicknessProvider,
)
from dodal.common.general_maths.material_absorption_maths import (
    MaterialAbsorptionSpectrum,
    attenuation_from_natural_log_of_transmission,
)
from dodal.common.general_maths.transmission_interconversion import (
    CANONICAL_NON_ABSORPTION,
)


@runtime_checkable
class FixedDepth(Protocol):
    def calculate_absorption_bn(self, *, xray_energy_kev: float) -> float:
        """Calculates absorption for a flat absorber of fixed depth.

        Typical use case is a foil absorber in a filter wheel.

        Args:
            xray_energy_kev: The energy of the x-ray photons in kiloelectonvolts.

        Returns:
            Absorption in the logarithmic Barnett units (Bn).
            N.B. logarithmic absorption units are used for system attenuation budget calculations.
        """
        ...


class AbsentFixedDepth(FixedDepth):
    """Fixed Depth aborber implementation for the absence of a foil in a filter wheel.

    Args:
        xray_energy_kev: The energy of the x-ray photons in kiloelectonvolts.

    Returns:
            Canonical value for not absorbing (in the logarithmic Barnett units, Bn).
            N.B. logarithmic absorption units are used for system attenuation budget calculations.
    """

    @validate_call
    def calculate_absorption_bn(self, *, xray_energy_kev: float) -> float:
        return CANONICAL_NON_ABSORPTION


@runtime_checkable
class VariableDepth(Protocol):
    def calculate_absorption_bn(
        self,
        *,
        xray_energy_kev: float,
        motor_position_mm: float,
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


class Absorber(BaseModel):
    """Base class for individual attenuating absorber.

    This is a system level entity in the business logic of a transmission subsystem,
    combines geometry and material absorption models, to yield attenuation calculations.
    N.B. natural units are cm for depth of absorber and logarithmic absorption units.

    Attributes:
        material_absorption_model: Material specific model for photon mass attenuation calculation.
    """

    spectrum: MaterialAbsorptionSpectrum
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    def _attenuation_bn(self, *, xray_energy_kev, thickness_cm):
        """Common internal conversion calculator.

        Extracts material photon mass attenuation from material calculator,
        and with the input thickness, derives the logarithmic attenuation.

        Args:
            xray_energy_kev: Energy of x-ray photons (kiloelectronvolts).
            thickness_cm: Material depth of the absorber (cm).

        Returns:
            Attenuation in 'system budget friendly' logarithmic units (Barnett units, Bn).
        """
        _alpha = self.spectrum.absorption_coefficient_per_cm(energy_kev=xray_energy_kev)
        _ln_t = -(thickness_cm * _alpha)
        return attenuation_from_natural_log_of_transmission(_ln_t)


class FoilAbsorber(Absorber):
    """System level representation of an foil absorbing filter, typically wheel mounted.

    Attributes:
        geometry_model: Shape model implementing the ThicknessProvider protocol.

    Returns:
            Attenuation in 'system budget friendly' logarithmic units (Barnett units, Bn).
    """

    geometry_model: ThicknessProvider

    @validate_call
    def calculate_absorption_bn(self, *, xray_energy_kev: StrictFloat) -> float:
        # see Protocol API for FixedDepth (absorber)
        _thickness_cm = self.geometry_model.get_thickness_cm()
        return self._attenuation_bn(
            xray_energy_kev=xray_energy_kev, thickness_cm=_thickness_cm
        )


class WedgeAbsorber(Absorber):
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
        *,
        xray_energy_kev: StrictFloat,
        motor_position_mm: StrictFloat,
    ) -> float:
        # see Protocol API for VariableDepth (absorber)
        _thickness_cm = self.geometry_model.thickness_cm_at_motor_position_mm(
            motor_position_mm=motor_position_mm
        )
        return self._attenuation_bn(
            xray_energy_kev=xray_energy_kev, thickness_cm=_thickness_cm
        )
