
from unittest.mock import MagicMock

import pytest

from dodal.devices.beamlines.i19.transmission.tx_domain_logic import (
    RetractableAttenuator,
    transparent_if_retracted,
)

# Test the bypass decorator transparent_if_retracted

class MockWedge(RetractableAttenuator[float]):
    def __init__(self, retraction_position: float) -> None:
        self.calculation_spy = MagicMock(return_value=46.89)
        self._retraction_pos = retraction_position
        self.retraction_spy = MagicMock(
            side_effect = lambda *, position: position < retraction_position
        )

    def readout(self) -> float:
        return 52.5

    def is_retracted_at_position(self, *, position: float) -> bool:
        return self.retraction_spy(position=position)

    @transparent_if_retracted
    def check_attenuation(self, position:float, *, energy_kev: float) -> float:
        return self.calculation_spy(energy_kev=energy_kev)


class MockWheel(RetractableAttenuator[int]):
    def __init__(self, retraction_index: int) -> None:
        self.calculation_spy = MagicMock(return_value=46.89)
        self._retraction_index = retraction_index
        self.retraction_spy = MagicMock(
            side_effect = lambda *, position: position == retraction_index
        )

    def readout(self) -> int:
        return 1

    def is_retracted_at_position(self, *, position: int) -> bool:
        return self.retraction_spy(position=position)

    @transparent_if_retracted
    def check_attenuation(self, index:int, *, energy_kev: float) -> float:
        return self.calculation_spy(energy_kev=energy_kev)


@pytest.mark.parametrize("out_position", [-8.3, 5.2, 14.93, 8.3, 65.2, 114.93])
def test_that_attenuator_asks_for_retraction_status_when_attenuation_requested(*, out_position: float) -> None:
    attenuator = MockWedge(retraction_position=out_position)
    attenuator.retraction_spy.assert_not_called()
    attenuator.check_attenuation(energy_kev=12345.7)
    attenuator.retraction_spy.assert_called_once()

@pytest.mark.parametrize("out_position", [58.3, 65.2, 114.93])
def test_that_attenuator_bypasses_calculator_when_absorber_retracted(out_position: float) -> None:
    attenuator = MockWedge(retraction_position=out_position)
    attenation_result:float = attenuator.check_attenuation(energy_kev=12345.7)
    attenuator.calculation_spy.assert_not_called()
    assert attenation_result == pytest.approx(0.0)


@pytest.mark.parametrize("out_position", [-8.3, 5.2, 14.93])
def test_that_attenuator_uses_calculator_when_absorber_not_retracted(*, out_position: float) -> None:
    attenuator = MockWedge(retraction_position=out_position)
    attenuator.calculation_spy.assert_not_called()
    attenuation_result:float = attenuator.check_attenuation(energy_kev=12345.7)
    attenuator.calculation_spy.assert_called()
    assert attenuation_result == pytest.approx(46.89)


@pytest.mark.parametrize("index", range(1,9))
def test_that_wheel_asks_for_retraction_status_when_attenuation_requested(*, index:int) -> None:
    attenuator = MockWheel(retraction_index=3)
    attenuator.retraction_spy.assert_not_called()
    attenuator.check_attenuation(energy_kev=12345.7)
    attenuator.retraction_spy.assert_called_once()


def test_that_wheel_bypasses_calculator_when_absorber_retracted() -> None:
    attenuator = MockWheel(retraction_index=1)
    attenation_result:float = attenuator.check_attenuation(energy_kev=12345.7)
    attenuator.calculation_spy.assert_not_called()
    assert attenation_result == pytest.approx(0.0)


@pytest.mark.parametrize("index_for_out", range(2,9))
def test_that_wheel_uses_calculator_when_absorber_not_retracted(*, index_for_out: int) -> None:
    attenuator = MockWheel(retraction_index=index_for_out)
    attenuator.calculation_spy.assert_not_called()
    attenuation_result:float = attenuator.check_attenuation(energy_kev=12345.7)
    attenuator.calculation_spy.assert_called()
    assert attenuation_result == pytest.approx(46.89)
