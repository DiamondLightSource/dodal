from functools import cached_property
from typing import Any, Final

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictFloat,
    StrictInt,
    computed_field,
    model_validator,
)
from pydantic.dataclasses import dataclass

from dodal.common.general_maths.absorber_geometry import (
    FoilGeometry,
    ThicknessProvider,
    WedgeGeometry,
)
from dodal.common.general_maths.absorbers import (
    AbsentFixedDepth,
    FixedDepth,
    FoilAbsorber,
    MaterialAbsorptionSpectrum,
    VariableDepth,
    WedgeAbsorber,
)
from dodal.common.general_maths.interval import ClosedInterval
from dodal.common.general_maths.material_absorption_maths import (
    AbsorptionCalculator,
    AbsorptionSpectrumSegment,
    CompoundAbsorptionCalculator,
    PolynomialAbsorptionCorrection,
    SingleRollOffAbsorptionCalculator,
)
from dodal.devices.beamlines.i19.access_controlled.attenuator_motor_squad import (
    PermittedKeyStr,
)


@dataclass(kw_only=True, frozen=True)
class EnergyDependenceSpecification:
    """Fit parameters for an absorption trend over a matched interval of x-ray energies.

    See modelling description on confluence: https://confluence.diamond.ac.uk/x/bAA6Dw

    Attributes:
        valid_energy_interval_kev: interval of x-ray energies, where the fit is considered valid.
        photon_absorption: photoelectric absorption - mass attenuation constant
        roll_off: exponent (negative valued) for decrease in absorption with respect to photon energy.
    """

    valid_energy_interval_kev: ClosedInterval
    photon_absorption: StrictFloat
    roll_off: StrictFloat

    @cached_property
    def _build_calculator(self) -> AbsorptionCalculator:
        return SingleRollOffAbsorptionCalculator(
            material_factor_per_cm=self.photon_absorption, roll_off=self.roll_off
        )

    def build_spectrum_segment(self) -> AbsorptionSpectrumSegment:
        return AbsorptionSpectrumSegment(
            kev_energy_interval=self.valid_energy_interval_kev,
            absorption_calculator=self._build_calculator,
        )


@dataclass(kw_only=True, frozen=True)
class CorrectedEnergyDependenceSpecification(EnergyDependenceSpecification):
    """Fit parameters for an absorption trend, with residual corrections, over a matched interval of x-ray energies.

    See modelling description on confluence: https://confluence.diamond.ac.uk/x/bAA6Dw

    Attributes:
        polynomial_correction_coefficients: coefficients (zeroth order first) for corrective polynomial
    """

    polynomial_correction_coefficients: tuple[StrictFloat, ...] = Field(
        default_factory=tuple,
        description="Coefficients of the fitted polynomial for fit curve corrective residuals",
        min_length=3,
    )

    @cached_property
    def _build_absorption_correction(self) -> PolynomialAbsorptionCorrection:
        _listed_coefficients = list(self.polynomial_correction_coefficients)
        return PolynomialAbsorptionCorrection(coefficients_per_cm=_listed_coefficients)

    @cached_property
    def _build_calculator(self) -> AbsorptionCalculator:
        return CompoundAbsorptionCalculator(
            contributions=[
                self._build_absorption_correction,
                super()._build_calculator,
            ]
        )


@dataclass(kw_only=True, frozen=True)
class AbsorptionSpectrumSpecification:
    """Specification for piecewise absorption spectrum of a particular material.

    A set of AbsorptionCurveSpec instances tied to a specific material used in absorbers.

    Attributes:
        material_model: Name of the material whose absorption spectrum is modelled, e.g. "Aluminium6061"
        spectral_segments: Fitted absorption trends for specific energy intervals.

    """

    material_model: str
    spectral_segments: tuple[EnergyDependenceSpecification, ...]

    def build_material_spectrum(self) -> MaterialAbsorptionSpectrum:
        _modelled_intervals: tuple[AbsorptionSpectrumSegment, ...] = tuple(
            segment.build_spectrum_segment() for segment in self.spectral_segments
        )
        return MaterialAbsorptionSpectrum(intervals=_modelled_intervals)


@dataclass(kw_only=True, frozen=True)
class WedgeMotorScaleSpecification:
    """Specification of motor details for a specific wedge absorber.

    N.B. The motor scale is the reference frame for the wedge geometry tip location.
    N.B. The names of these positions comes from domain scientists preferred domain specific jargon.

    Attributes:
        axis: Tag label of the motor axis direction (e.g. "y")
        maximum: Permitted motor position where wedge (in beam) is thickest.  (Not necessarily the most positive motor position).
        out: Motor position for which the absorber is in the canonical OUT position.
        threshold: Permitted motor position where wedge (in beam) is thinnest.
        tip: The motor position where modelled wedge would have zero thickness
        units: Motor position distance unit, typically "mm".
    """

    axis_label: PermittedKeyStr  # Name used in motor position requests
    maximum: StrictFloat  # Motor position to place maximal usable absorber thickness into the x-ray beam
    out: StrictFloat  # Motor position controls team use to remove absorber from the x-ray beam entirely
    threshold: StrictFloat  # Motor position to place minimal usable absorber thickness into the x-ray beam
    tip: StrictFloat  # Motor position corresponding to mathematically modelled zero thickness of wedge taper in x-ray beam
    units: str = "mm"  # Motor scale distance units
    _margin: Final[float] = 5.0e-3  # Five microns lee-way for motor position checking

    @computed_field
    @cached_property
    def has_positive_sense(self) -> bool:
        return self.maximum > self.threshold

    @computed_field
    @cached_property
    def active_position_range(self) -> ClosedInterval:
        a = min(self.threshold, self.maximum)
        b = max(self.threshold, self.maximum)
        return ClosedInterval(lower=a, upper=b)

    @model_validator(mode="after")
    def _verify_internal_consistency(self) -> "WedgeMotorScaleSpecification":
        _lower, _upper = (
            (self.out, self.threshold)
            if self.has_positive_sense
            else (self.threshold, self.out)
        )
        _consistency_interval = ClosedInterval(lower=_lower, upper=_upper)

        if self.tip not in _consistency_interval:
            _msg = f"Wedge motor scale spec for {self.axis_label}, has inconsistent order for out: {self.out}, tip: {self.tip} and threshold: {self.threshold}."
            raise ValueError(_msg)
        return self

    def is_consistent_with_absorber_out(self, *, motor_position: StrictFloat) -> bool:
        _lower_margin = self.out - abs(self._margin)
        _upper_margin = self.out + abs(self._margin)
        _out_interval = ClosedInterval(lower=_lower_margin, upper=_upper_margin)
        return motor_position in _out_interval


@dataclass(kw_only=True, frozen=True)
class FlatFoilThicknessSpecification:
    """Foil thickness specification for a flat foil x-ray absorbing attenuator, usually wheel mounted.

    N.B. The specification provides a quantity in one of the supported thickness units,
    namely cm, mm, micron, um.  (See general_maths.absorber_geometry.SupportedThicknessUnits)

    Attributes:
        thickness_value: The numerical part of the foil thickness.
        thichness_units: The units part of the foil thickness.
    """

    thickness_value: StrictFloat
    thickness_unit: str

    def build_thickness_provider(self) -> ThicknessProvider:
        return FoilGeometry(
            unit=self.thickness_unit, numerical_value=self.thickness_value
        )


@dataclass(kw_only=True, frozen=True)
class ThinWedgeTaperSpecification:
    """Taper angle specification for a modelled wedge shape.

    N.B. The physical shape of the wedge is different from this mathematical simplification.

    Attributes:
        taper_cotangent: The taper angle specified as the cotangent (which will be larger than 5 for thin wedges).
    """

    taper_cotangent: StrictFloat


class AbsorberSlotSpecification(BaseModel):
    """Specification for filter wheel slot, defaults to out of bounds status.

    Attributes:
        wheel_identifier: Tag or other recognisable name for the host wheel where this slot is found.
        slot_index: integer used to index and identify the slot, if not specified.
    """

    wheel_identifier: str
    slot_index: StrictInt

    @cached_property
    def slot_identifier(self) -> str:
        return (
            f"Attenuating filter wheel {self.wheel_identifier} slot {self.slot_index}"
        )

    model_config = ConfigDict(frozen=True)

    def is_in_use(self) -> bool:
        return False

    @cached_property
    def installed_foil(self) -> FixedDepth:
        """Raises:
        Default ValueError - indicating which slot is not in use.
        """
        raise ValueError(f"{self.slot_identifier} is not configured for use.")


class UsedSlotSpecification(AbsorberSlotSpecification):
    """Specification for filter wheel slot, defaults to utilised empty slot."""

    def is_in_use(self) -> bool:
        return True

    @cached_property
    def installed_foil(self) -> FixedDepth:
        """Default to empty slots absent absorber type."""
        return AbsentFixedDepth()


class InstalledUsedSlotSpecification(UsedSlotSpecification):
    """Specification for slots with installed flat foil absorbers operationally permitted for use.

    Attributes:
        absorber_thickness: The thickness a flat absorbing foil.
        material_spectrum: The absorbing material spectrum specification.
    """

    absorber_thickness: ThicknessProvider
    material_spectrum: MaterialAbsorptionSpectrum

    @cached_property
    def installed_foil(self) -> FixedDepth:
        return FoilAbsorber(
            geometry_model=self.absorber_thickness,
            spectrum=self.material_spectrum
        )


class WheelSlotSpecifier(BaseModel):
    wheel_identifier: str

    model_config = ConfigDict(frozen=True)

    def specify_slot_in_use_but_empty_at_index(
        self, slot_index: int
    ) -> UsedSlotSpecification:
        return UsedSlotSpecification(
            wheel_identifier=self.wheel_identifier, slot_index=slot_index
        )

    def specify_empty_slot_out_of_bounds_at_index(
        self, slot_index: int
    ) -> AbsorberSlotSpecification:
        return AbsorberSlotSpecification(
            wheel_identifier=self.wheel_identifier, slot_index=slot_index
        )

    def specify_foil_in_slot_out_of_bounds_at_index(
        self,
        slot_index: int,
        *,
        spectrum_specification: AbsorptionSpectrumSpecification,
        foil_shape: FlatFoilThicknessSpecification,
    ) -> AbsorberSlotSpecification:
        return AbsorberSlotSpecification(
            wheel_identifier=self.wheel_identifier, slot_index=slot_index
        )

    def specify_foil_in_slot_at_index(
        self,
        slot_index: int,
        *,
        spectrum_specification: AbsorptionSpectrumSpecification,
        foil_shape: FlatFoilThicknessSpecification,
    ) -> InstalledUsedSlotSpecification:
        _material_spectrum: MaterialAbsorptionSpectrum = (
            spectrum_specification.build_material_spectrum()
        )
        _geometry_model: ThicknessProvider = foil_shape.build_thickness_provider()
        return InstalledUsedSlotSpecification(
            wheel_identifier=self.wheel_identifier,
            slot_index=slot_index,
            material_spectrum=_material_spectrum,
            absorber_thickness=_geometry_model,
        )


class WheelOccupancySpecification(BaseModel):
    """Wheel occupancy maps names of slots (as given in filter_selections.py) to specific filters/absences.

    Attributes:
        registration: dictionary of slot names from filter_selections versus absorber specifications,
            with vacancies indicated by a specific vacancy specification type.
    """

    registration: dict[Any, AbsorberSlotSpecification] = Field(
        description="Complete indication of occupation state of all slots in a filter wheel."
    )
    model_config = ConfigDict(frozen=True)

    @cached_property
    def operational_absorbers(self) -> dict[int, FixedDepth]:
        return {
            v.slot_index: v.installed_foil
            for v in self.registration.values()
            if v.is_in_use()
        }


class WedgeAbsorberSpecification(BaseModel):
    """Specification for a wedge absorber, combines material, positions and shape.

    Attributes:
        exclusions: Motor position intervals (Optional)
            within the active absorbing motor range that should be avoided.

        shape: The thin taper shape specification.
        motor_coordinates: Specific operational positions on the linear motors axis scale.
    """
    exclusions: tuple[ClosedInterval, ...] = Field(
        description="(Optional) motor position intervals within the absorber range to avoid,",
        default_factory=tuple,
    )

    material_spectrum: MaterialAbsorptionSpectrum
    motor_coordinates: WedgeMotorScaleSpecification = Field(
        description="Specific operational positions on the linear motors axis scale."
    )
    shape: ThinWedgeTaperSpecification = Field(
        description="The thin taper shape specification."
    )

    model_config = ConfigDict(frozen=True)

    @model_validator(mode="after")
    def verify_internal_consistency(self) -> "WedgeAbsorberSpecification":
        if not all(
            excluded_interval in self.motor_coordinates.active_position_range
            for excluded_interval in self.exclusions
        ):
            raise RuntimeError(
                "Wedge specification features an exclusion interval beyond the canonical wedge absorber position range"
            )
        return self

    def build_absorber(self) -> VariableDepth:
        _geometry_model = WedgeGeometry(tip_mm=self.motor_coordinates.tip,
                                        taper_cotangent=self.shape.taper_cotangent)
        return WedgeAbsorber(spectrum=self.material_spectrum,
                             geometry_model=_geometry_model)
