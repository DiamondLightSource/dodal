from unittest.mock import MagicMock

from dodal.common.general_maths.absorber_geometry import (
    TaperedGeometryProvider,
    ThicknessProvider,
)
from dodal.common.general_maths.absorbers import FoilAbsorber, WedgeAbsorber
from dodal.common.general_maths.material_absorption_maths import (
    SingleRollOffAbsorptionCalculator,
)

# happy path


def test_that_wedge_absorber_asks_geometry_model_for_thickness():
    material_absorption_strut = MagicMock(spec=SingleRollOffAbsorptionCalculator)
    material_absorption_strut.absorption_coefficient_per_cm.return_value = 1.9
    geometry_model = MagicMock(spec=TaperedGeometryProvider)
    geometry_model.taper_cotangent = 12.3
    geometry_model.thickness_cm_at_motor_position_mm.return_value = 0.5
    wedge_absorber = WedgeAbsorber(
        material_absorption_model=material_absorption_strut,
        geometry_model=geometry_model,
    )
    wedge_absorber.calculate_absorption_bn(
        xray_energy_kev=12345.0, motor_position_mm=1.0
    )
    geometry_model.thickness_cm_at_motor_position_mm.assert_called_once_with(1.0)


def test_that_foil_absorber_asks_geometry_model_for_thickness():
    material_absorption_strut = MagicMock(spec=SingleRollOffAbsorptionCalculator)
    material_absorption_strut.absorption_coefficient_per_cm.return_value = 1.8
    geometry_model = MagicMock(spec=ThicknessProvider)
    geometry_model.get_thickness_cm.return_value = 0.5
    foil_absorber = FoilAbsorber(
        material_absorption_model=material_absorption_strut,
        geometry_model=geometry_model,
    )
    foil_absorber.calculate_absorption_bn(xray_energy_kev=12345.0)
    geometry_model.get_thickness_cm.assert_called_once()
