from typing import Any

from dodal.common.general_maths.absorbers import VariableDepth


class SpecifiedWedgeModel:
    def __init__(self, *, specifications: Any):
        self.calculator: VariableDepth = self._build_calculator(
            specifications=specifications
        )
        self.is_out = lambda p: abs(p - specifications.out) < specifications.tolerance

    def _build_calculator(self, *, specifications) -> VariableDepth: ...

    def _get_threshold(self) -> float: ...

    def calculate_absorption_bn(
        self,
        *,
        xray_energy_kev: float,
        motor_position_mm: float,
    ) -> float:
        return self.calculator.calculate_absorption_bn(
            xray_energy_kev=xray_energy_kev, motor_position_mm=motor_position_mm
        )

    def fulcrum_attenuation_bn(self, *, energy_kev: float) -> float:
        return self.calculate_absorption_bn(
            xray_energy_kev=energy_kev, motor_position_mm=self._get_threshold()
        )

    def is_wedge_out(self, a_motor_position_mm: float) -> bool:
        return self.is_out(a_motor_position_mm)
