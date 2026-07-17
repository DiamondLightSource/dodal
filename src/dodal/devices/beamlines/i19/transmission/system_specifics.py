

from pydantic import StrictFloat, validate_call
from pydantic.dataclasses import dataclass

from dodal.common.general_maths.absorber_geometry import WedgeGeometry
from dodal.common.general_maths.absorbers import (
    FixedDepth,
    WedgeAbsorber,
    WedgeMotorScaleSpec,
    XrayEnergy,
)
from dodal.common.general_maths.material_absorption_maths import (
    SingleRollOffAbsorptionCalculator,
)
from dodal.common.general_maths.transmission_interconversion import (
    CANONICAL_NON_ABSORPTION,
    Attenuation_Bn,
)
from dodal.devices.beamlines.i19.access_controlled.attenuator_motor_squad import (
    AttenuatorMotorPositions,
)

from .tx_types import (
    AttenuatorSubsystem,
    EmptyFilterSlot,
    FixedDepth,
    IndexedFilterSet,
    IndexReader,
    PositionReader,
    Wedge,
    Wheel,
    Wheel_Index,
    XrayEnergy,
)

# Specific details of the I19 set-up
# General types in tx_types.py

@dataclass(kw_only=True, frozen=True)
class AttenXMotorScale(WedgeMotorScaleSpec):

    # TODO make these injected from external source of ground truth not hardwired here
    out_mm: StrictFloat = 0.1
    tip_mm: StrictFloat = -3.959
    threshold_mm: StrictFloat = 1.5
    max_mm: StrictFloat = 75.0


@dataclass(kw_only=True, frozen=True)
class AttenYMotorScale(WedgeMotorScaleSpec):

    # TODO make these injected from external source of ground truth not hardwired here
    out_mm: StrictFloat = 5.0
    threshold_mm: StrictFloat = 8.9
    max_mm: StrictFloat = 98.0

@dataclass(kw_only=True)
class AluminiumWedgeGeometry(WedgeGeometry):
    # TODO make this frozen - by modifying parent Geometry class
    # TODO make these injected from external source of ground truth not hardwired here

    tip_mm: StrictFloat = 5.06
    taper_cotangent: StrictFloat = 9.3985


class WheelOneFilterSet(IndexedFilterSet):

    def __init__(self):
        self._empty_slot_equivalent_absorber: FixedDepth = EmptyFilterSlot()
        self._canonical_empty_slot: Wheel_Index = 1 # AIR1

    def _canonical_wheel_name(self) -> str:
        return "Filter Wheel One"


    def _get_populated_slot_indices(self) -> set[Wheel_Index]:
        return set()  # TODO populate these by reverse engineering content of filter_selections - when wheel works


    def canonical_index_for_absorbers_out_of_beam(self) -> Wheel_Index:
        return self._canonical_empty_slot


    @validate_call
    def are_absorbers_out_of_beam_at_index(self, index: Wheel_Index) -> bool:
        return self.canonical_index_for_absorbers_out_of_beam == index


    @validate_call
    def filter_at(self, index: Wheel_Index) -> FixedDepth:
        match index:
            case self._canonical_empty_slot:
                return self._empty_slot_equivalent_absorber
            case _ if index in self._get_populated_slot_indices():
                _not_implemented_msg = "Populated slots are presently unsupported in {self._get_wheel_name()}"
                raise NotImplementedError(_not_implemented_msg)
            case _:
                _unused_msg = f"{self._canonical_wheel_name()}, does not use slot {index}."
                raise ValueError(_unused_msg)


class WheelOneIndexReader(IndexReader):

    def read_motor_index(self) -> Wheel_Index:
        # TODO make something that has this API function
        # which can digest the filter set but report index position
        # for now, while the wheel is out of action this is an MVP
        # I understand that the existing (established) FilterWheel class might
        # take the job on at some point
        return 1


class AluminiumWedgePositionReader(PositionReader):

    def read_motor_position_mm(self) -> StrictFloat:
        return 0.0  # TODO hook this up to read from the real motor position


class PrimaryAttenuators(AttenuatorSubsystem):

    # Binds filter wheel and aluminium Y wedge into one business logic unit
    def __init__(
        self,
    ):
        # build filter wheel representation
        _filter_set_for_wheel_one = WheelOneFilterSet()
        _wheel_motor_key = "w"
        _index_reader = WheelOneIndexReader()
        self.wheel_one = Wheel(recognised_filters=_filter_set_for_wheel_one,
                               motor_key=_wheel_motor_key,
                               index_reader=_index_reader)
        # build aluminium wedge representation
        _y_motor_scale = AttenYMotorScale()
        _y_motor_key = "y"
        _y_motor_reader = AluminiumWedgePositionReader()
        # TODO replace this hardwired magic number instance with something settable
        _aluminium_calculator = SingleRollOffAbsorptionCalculator(material_factor_per_cm=6.4873e4,
                                                                  roll_off=-2.96)
        _wedge_geometry = AluminiumWedgeGeometry()
        _aluminium_absorber = WedgeAbsorber(material_absorption_model=_aluminium_calculator,
                                            geometry_model=_wedge_geometry)
        self.aluminium_wedge = Wedge(motor_scale=_y_motor_scale,
                                     motor_key=_y_motor_key,
                                     position_reader=_y_motor_reader,
                                     absorber=_aluminium_absorber)

    def is_in_the_out_position(self) -> bool:
        return self.wheel_one.is_in_the_out_position() and self.aluminium_wedge.is_in_the_out_position()

    def calculate_attenuation_bn(
        self,
        *,
        xray_energy_kev: XrayEnergy,
        attenuator_positions: AttenuatorMotorPositions,
    ) -> Attenuation_Bn:
        if self.is_in_the_out_position:
            return CANONICAL_NON_ABSORPTION
        else:
            _wheel_contribution = self.wheel_one.calculate_attenuation_bn(xray_energy_kev=xray_energy_kev,
                                                                        attenuator_positions=attenuator_positions)
            _wedge_contribtion = self.aluminium_wedge.calculate_attenuation_bn(xray_energy_kev=xray_energy_kev,
                                                                            attenuator_positions=attenuator_positions)
            return _wheel_contribution + _wedge_contribtion
