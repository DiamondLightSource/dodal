from typing import Final

from dodal.devices.attenuator.filter_selections import I19FilterOneSelections
from dodal.devices.beamlines.i19.transmission.specific_absorber_materials import (
    MATERIAL_ABSORPTION_SPECTRUM_ALUMINIUM_2,
    MATERIAL_ABSORPTION_SPECTRUM_GOLD_1,
    MATERIAL_ABSORPTION_SPECTRUM_IRON_1,
)
from dodal.devices.beamlines.i19.transmission.specification_types import (
    AbsorberSlotSpecification,
    FlatFoilThicknessSpecification,
    WheelOccupancySpecification,
    WheelSlotSpecifier,
)

factory_w1 = WheelSlotSpecifier(wheel_identifier="W1")


THICKNESS_SPECIFICATION_ALUMINIUM_FOIL_TWO: Final = (
    FlatFoilThicknessSpecification(thickness_unit="mm", thickness_value=6.0)
)

THICKNESS_SPECIFICATION_IRON_FOIL_ONE: Final = (
    FlatFoilThicknessSpecification(thickness_unit="mm", thickness_value=0.5)
)

THICKNESS_SPECIFICATION_GOLD_FOIL_ONE: Final = (
    FlatFoilThicknessSpecification(thickness_unit="um", thickness_value=25)
)

# Replace specify_foil_in_slot_out_of_bounds_at_index -> specify_foil_in_slot_at_index
# to activate any foil bearing slot

SLOTS_IN_WHEEL_ONE: Final[dict[I19FilterOneSelections, AbsorberSlotSpecification]] = {
    I19FilterOneSelections.W1S1: factory_w1.specify_slot_in_use_but_empty_at_index(1),
    I19FilterOneSelections.W1S2: factory_w1.specify_foil_in_slot_out_of_bounds_at_index(2,
        spectrum_specification=MATERIAL_ABSORPTION_SPECTRUM_ALUMINIUM_2,
        foil_shape=THICKNESS_SPECIFICATION_ALUMINIUM_FOIL_TWO,
    ),
    I19FilterOneSelections.W1S3: factory_w1.specify_empty_slot_out_of_bounds_at_index(3),
    I19FilterOneSelections.W1S4: factory_w1.specify_foil_in_slot_out_of_bounds_at_index(4,
        spectrum_specification=MATERIAL_ABSORPTION_SPECTRUM_IRON_1,
        foil_shape=THICKNESS_SPECIFICATION_IRON_FOIL_ONE,
    ),
    I19FilterOneSelections.W1S5: factory_w1.specify_empty_slot_out_of_bounds_at_index(5),
    I19FilterOneSelections.W1S6: factory_w1.specify_foil_in_slot_out_of_bounds_at_index(6,
        spectrum_specification=MATERIAL_ABSORPTION_SPECTRUM_GOLD_1,
        foil_shape=THICKNESS_SPECIFICATION_GOLD_FOIL_ONE,
    ),
}

FILTER_WHEEL_1_OCCUPANCY:Final = WheelOccupancySpecification(registration=SLOTS_IN_WHEEL_ONE)
