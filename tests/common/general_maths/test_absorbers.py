import math
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

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
        xray_energy_kev=12.345,
        motor_position_mm=4.2,  # energy irrelevant
    )
    geometry_model.thickness_cm_at_motor_position_mm.assert_called_once_with(
        motor_position_mm=4.2
    )


def test_that_wedge_absorber_reports_faithful_absorption_result():
    material_absorption_strut = MagicMock(spec=SingleRollOffAbsorptionCalculator)
    material_absorption_strut.absorption_coefficient_per_cm.return_value = 2.5
    geometry_model = MagicMock(spec=TaperedGeometryProvider)
    geometry_model.taper_cotangent = 19.1
    geometry_model.thickness_cm_at_motor_position_mm.return_value = 0.72
    wedge_absorber = WedgeAbsorber(
        material_absorption_model=material_absorption_strut,
        geometry_model=geometry_model,
    )
    result = wedge_absorber.calculate_absorption_bn(
        xray_energy_kev=16.0932,
        motor_position_mm=15.0,  # energy, motor position irrelevant
    )
    expected_result = 1800.0  # 0.72cm * 2.5 alpha per cm * 1000 Bn per 1/e factor
    assert result == pytest.approx(expected_result)


def test_that_foil_absorber_asks_geometry_model_for_thickness():
    material_absorption_strut = MagicMock(spec=SingleRollOffAbsorptionCalculator)
    material_absorption_strut.absorption_coefficient_per_cm.return_value = 1.8
    geometry_model = MagicMock(spec=ThicknessProvider)
    geometry_model.get_thickness_cm.return_value = 0.5
    foil_absorber = FoilAbsorber(
        material_absorption_model=material_absorption_strut,
        geometry_model=geometry_model,
    )
    foil_absorber.calculate_absorption_bn(xray_energy_kev=12.3450)  # energy irrelevant
    geometry_model.get_thickness_cm.assert_called_once()


def test_that_foil_absorber_reports_faithful_absorption_result():
    material_absorption_strut = MagicMock(spec=SingleRollOffAbsorptionCalculator)
    material_absorption_strut.absorption_coefficient_per_cm.return_value = 0.63
    geometry_model = MagicMock(spec=ThicknessProvider)
    geometry_model.get_thickness_cm.return_value = 0.85
    foil_absorber = FoilAbsorber(
        material_absorption_model=material_absorption_strut,
        geometry_model=geometry_model,
    )
    result = foil_absorber.calculate_absorption_bn(
        xray_energy_kev=21.9514
    )  # energy irrelevant
    expected_result = 535.5  # 0.85 cm * 0.63 alpha per cm * 1000 Bn per 1/e factor
    assert result == pytest.approx(expected_result)


# Inauspicious path


@pytest.mark.parametrize(
    "invalid_xray_energy",
    [
        None,
        78,
        106.7,
        -21.4501,
        -8,
        0.02,
        "",
        "J",
        object(),
        math.sin,
        KeyError(),
        False,
        True,
    ],
)
def test_that_foil_absorber_reports_raises_error_when_xray_energy_is_invalid(
    invalid_xray_energy,
):
    material_absorption_strut = MagicMock(spec=SingleRollOffAbsorptionCalculator)
    material_absorption_strut.absorption_coefficient_per_cm.return_value = 0.63
    geometry_model = MagicMock(spec=ThicknessProvider)
    geometry_model.get_thickness_cm.return_value = 0.85
    foil_absorber = FoilAbsorber(
        material_absorption_model=material_absorption_strut,
        geometry_model=geometry_model,
    )
    with pytest.raises(ValidationError):
        foil_absorber.calculate_absorption_bn(xray_energy_kev=invalid_xray_energy)


@pytest.mark.parametrize(
    "invalid_xray_energy",
    [
        None,
        42,
        50.6,
        -21.4501,
        -6,
        0.04,
        "",
        "o",
        object(),
        math.log1p,
        KeyError(),
        False,
        True,
    ],
)
def test_that_wedge_absorber_reports_raises_error_when_xray_energy_is_invalid(
    invalid_xray_energy,
):
    material_absorption_strut = MagicMock(spec=SingleRollOffAbsorptionCalculator)
    material_absorption_strut.absorption_coefficient_per_cm.return_value = 2.5
    geometry_model = MagicMock(spec=TaperedGeometryProvider)
    geometry_model.taper_cotangent = 19.1
    geometry_model.thickness_cm_at_motor_position_mm.return_value = 0.72
    wedge_absorber = WedgeAbsorber(
        material_absorption_model=material_absorption_strut,
        geometry_model=geometry_model,
    )
    with pytest.raises(ValidationError):
        wedge_absorber.calculate_absorption_bn(
            xray_energy_kev=invalid_xray_energy,
            motor_position_mm=12.8,  # energy, motor position irrelevant
        )


@pytest.mark.parametrize(
    "invalid_motor_position",
    [
        None,
        "",
        "M",
        object(),
        math.cos,
        KeyError(),
        False,
        True,
    ],
)
def test_that_wedge_absorber_reports_raises_error_when_motor_position_is_invalid(
    invalid_motor_position,
):
    material_absorption_strut = MagicMock(spec=SingleRollOffAbsorptionCalculator)
    material_absorption_strut.absorption_coefficient_per_cm.return_value = 2.5
    geometry_model = MagicMock(spec=TaperedGeometryProvider)
    geometry_model.taper_cotangent = 18.1
    geometry_model.thickness_cm_at_motor_position_mm.return_value = 0.62
    wedge_absorber = WedgeAbsorber(
        material_absorption_model=material_absorption_strut,
        geometry_model=geometry_model,
    )
    with pytest.raises(ValidationError):
        wedge_absorber.calculate_absorption_bn(
            xray_energy_kev=21.7,
            motor_position_mm=invalid_motor_position,  # energy, motor position irrelevant
        )
