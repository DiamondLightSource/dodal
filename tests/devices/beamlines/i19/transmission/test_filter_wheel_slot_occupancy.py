
import math
from typing import Any
from unittest.mock import MagicMock

import pytest

from dodal.common.general_maths.absorbers import FixedDepth
from dodal.common.general_maths.transmission_interconversion import (
    CANONICAL_NON_ABSORPTION,
)
from dodal.devices.beamlines.i19.transmission.filter_wheel_slot_occupancy import (
    FilterWheelSlotOccupancy,
    _CanonicalEmptySlot,
)


def test_that_filter_wheel_slot_occupancy_accepts_valid_setup_attributes() -> None:
    kwargs = {
        "wheel_name":"w",
        "wheel_capacity":6,
        "reserved_slot":1,
        "permitted_slots": [2, 4, 7,],
        "occupied_slots": {
            6: MagicMock(autospec=FixedDepth),
            4: MagicMock(autospec=FixedDepth),
        }
    }
    wheel_occupancy_example = FilterWheelSlotOccupancy(**kwargs)
    assert isinstance(wheel_occupancy_example, FilterWheelSlotOccupancy)


@pytest.mark.parametrize(
    "capacity",
    (
        6, 8, 16, 24,
    )
)
def test_that_filter_wheel_slot_occupancy_recognises_when_index_is_within_its_capacity(capacity:int) -> None:
    kwargs = {
        "wheel_name":"w",
        "wheel_capacity":capacity,
        "reserved_slot":1,
        "permitted_slots": [2, 4, 7,],
        "occupied_slots": {
            6: MagicMock(autospec=FixedDepth),
            4: MagicMock(autospec=FixedDepth),
        }
    }
    fwso = FilterWheelSlotOccupancy(**kwargs)
    for i in range(capacity):
        j: int = i + 1
        k: int = capacity + j
        assert fwso._is_beyond_wheel_capacity(slot=k)
        assert not fwso._is_beyond_wheel_capacity(slot=j)


@pytest.mark.parametrize(
    "capacity",
    (
        12, 6,
    )
)
def test_that_filter_wheel_slot_occupancy_recognises_when_index_exceeds_its_capacity(capacity:int) -> None:
    kwargs = {
        "wheel_name":"w",
        "wheel_capacity":capacity,
        "reserved_slot":1,
        "permitted_slots": [2, 4, 7,],
        "occupied_slots": {
            6: MagicMock(autospec=FixedDepth),
            4: MagicMock(autospec=FixedDepth),
        }
    }
    fwso = FilterWheelSlotOccupancy(**kwargs)
    k: int = capacity * 2 + 5
    assert fwso._is_beyond_wheel_capacity(slot=k)

@pytest.mark.parametrize(
    "strictly",
    (
        True, False,
    )
)
def test_that_wheel_slot_occupancy_recognises_reserved_slot_as_being_in_use(strictly: bool) -> None:
    kwargs = {
        "wheel_name":"w",
        "wheel_capacity":5,
        "reserved_slot":5,
        "permitted_slots": [1, 3,],
        "occupied_slots": {
            1: MagicMock(autospec=FixedDepth),
            3: MagicMock(autospec=FixedDepth),
            4: MagicMock(autospec=FixedDepth),
        }
    }
    fwso = FilterWheelSlotOccupancy(**kwargs)
    assert fwso.is_index_in_use(index=5, strict=strictly)


@pytest.mark.parametrize(
    "slot, in_use",
    [
        (4, False,),
        (1, True,),
        (3, False,),
        (5, True,),
        (2, False,),
    ]
)
def test_that_wheel_slot_occupancy_recognises_when_index_is_strictly_in_use(slot: int, in_use: bool) -> None:
    kwargs = {
        "wheel_name":"w",
        "wheel_capacity":6,
        "reserved_slot":6,
        "permitted_slots": [1, 5,],
        "occupied_slots": {
            1: MagicMock(autospec=FixedDepth),
            3: MagicMock(autospec=FixedDepth),
            5: MagicMock(autospec=FixedDepth),
        }
    }
    fwso = FilterWheelSlotOccupancy(**kwargs)
    assert in_use == fwso.is_index_in_use(index=slot, strict=True)


@pytest.mark.parametrize(
    "slot, has_foil",
    [
        (4, False,),
        (1, True,),
        (3, True,),
        (5, True,),
        (2, False,),
    ]
)
def test_that_wheel_slot_occupancy_recognises_when_index_has_a_declared_foil_filter(slot: int, has_foil: bool) -> None:
    kwargs = {
        "wheel_name":"w",
        "wheel_capacity":6,
        "reserved_slot":6,
        "permitted_slots": [1, 5,],
        "occupied_slots": {
            1: MagicMock(autospec=FixedDepth),
            3: MagicMock(autospec=FixedDepth),
            5: MagicMock(autospec=FixedDepth),
        }
    }
    fwso = FilterWheelSlotOccupancy(**kwargs)
    assert has_foil == fwso.is_index_in_use(index=slot, strict=False)


@pytest.mark.parametrize(
    "reserved_slot",
    ( 3, 1, 4, 5, 2, 6,)
)
def test_that_filter_wheel_picks_out_reserved_slot_calculator(reserved_slot:int) -> None:
    kwargs = {
        "wheel_name":"w",
        "wheel_capacity":6,
        "reserved_slot":reserved_slot,
        "permitted_slots": [7, 8, 9],
        "occupied_slots": {
        }
    }
    fwso = FilterWheelSlotOccupancy(**kwargs)
    calc: FixedDepth = fwso.absorption_calculator_of(index=reserved_slot)
    assert isinstance(calc, _CanonicalEmptySlot)


@pytest.mark.parametrize(
    "energy_kev",
    ( 1, 3.4, 5.16, 8.0912, 11.37, 12, 12.42789, 15.0421, 23.09, 25.772 )
)
def test_that_filter_wheel_reserved_slot_calculator_eligible_for_any_energy(energy_kev:float) -> None:
    kwargs = {
        "wheel_name":"w",
        "wheel_capacity":6,
        "reserved_slot":1,
        "permitted_slots": [],
        "occupied_slots": {
        }
    }
    fwso = FilterWheelSlotOccupancy(**kwargs)
    calc: FixedDepth = fwso.absorption_calculator_of(index=1)
    assert calc.is_eligible_for_energy(
        xray_energy_kev=energy_kev
    )


@pytest.mark.parametrize(
    "energy_kev",
    ( 2.04, 1.74, 5.16, 7.0912, 13.137, 14, 12.4789, 16.0421, 21.09, 24.712 )
)
def test_that_filter_wheel_reserved_slot_is_canonically_transparent(energy_kev:float) -> None:
    kwargs = {
        "wheel_name":"w",
        "wheel_capacity":6,
        "reserved_slot":3,
        "permitted_slots": [],
        "occupied_slots": {
        }
    }
    fwso = FilterWheelSlotOccupancy(**kwargs)
    calc: FixedDepth = fwso.absorption_calculator_of(index=3)
    assert calc.calculate_absorption_bn(
        xray_energy_kev=energy_kev
    ) is CANONICAL_NON_ABSORPTION


def test_that_filter_wheel_serves_up_requested_foil_calculator_when_permitted() -> None:
    sentinel_calc1 = MagicMock(autospec=FixedDepth)
    sentinel_calc2 = MagicMock(autospec=FixedDepth)
    kwargs = {
        "wheel_name":"w",
        "wheel_capacity":6,
        "reserved_slot":2,
        "permitted_slots": [1, 3, 4],
        "occupied_slots": {
            3: sentinel_calc1,
            4: sentinel_calc2,
        }
    }
    fwso = FilterWheelSlotOccupancy(**kwargs)

    assert sentinel_calc2 is fwso.absorption_calculator_of(index=4)
    assert sentinel_calc1 is not fwso.absorption_calculator_of(index=4)

    assert sentinel_calc1 is fwso.absorption_calculator_of(index=3)
    assert sentinel_calc2 is not fwso.absorption_calculator_of(index=3)


# Inauspicious path tests

@pytest.mark.parametrize(
    "invalid_id",
    [
        {},
        (),
        [],
        object(),
        KeyError,
        True,
        False,
        math.log1p,
        "",
        None,
        1,
        -8,
        92.2,
        -math.pi,
    ]
)
def test_that_error_raised_if_filter_wheel_slot_occupancy_instantiation_lacks_valid_wheel_identification(
    invalid_id: Any
) -> None:
    kwargs = {
        "wheel_name":invalid_id,
        "wheel_capacity":6,
        "reserved_slot":2,
        "permitted_slots": [1, 4, 3,],
        "occupied_slots": {
            1: MagicMock(autospec=FixedDepth),
            4: MagicMock(autospec=FixedDepth),
        }
    }
    with pytest.raises(ValueError):
        _probe = FilterWheelSlotOccupancy(**kwargs)


@pytest.mark.parametrize(
    "invalid_number_of_slots",
    [
        {},
        [],
        (),
        object(),
        RuntimeError,
        True,
        False,
        math.erfc,
        "",
        "Hello World",
        "Y",
        "*",
        "8",
        "-44",
        None,
        0,
        -6,
        0.51,
        57.2,
        -math.e,
    ]
)
def test_that_error_raised_if_filter_wheel_slot_occupancy_instantiation_has_no_valid_capacity(
    invalid_number_of_slots: Any
) -> None:
    kwargs = {
        "wheel_name":"w",
        "wheel_capacity": invalid_number_of_slots,
        "reserved_slot": 5,
        "permitted_slots": [2, 4, 3,],
        "occupied_slots": {
            7: MagicMock(autospec=FixedDepth),
            3: MagicMock(autospec=FixedDepth),
        }
    }
    with pytest.raises(ValueError):
        _probe = FilterWheelSlotOccupancy(**kwargs)


@pytest.mark.parametrize(
    "invalid_slot_reservation",
    [
        {},
        [],
        (),
        (1,4,),
        object(),
        RuntimeError,
        True,
        False,
        math.erfc,
        "",
        "Hello World",
        "Y",
        "*",
        "8",
        "-44",
        None,
        0,
        205,
        -3,
        0.51,
        57.2,
        -math.e,
    ]
)
def test_that_error_raised_if_filter_wheel_slot_occupancy_instantiation_lacks_valid_reserved_slot_index(
    invalid_slot_reservation: Any
) -> None:
    kwargs = {
        "wheel_name":"w",
        "wheel_capacity": 6,
        "reserved_slot": invalid_slot_reservation,
        "permitted_slots": [2, 4, 3,],
        "occupied_slots": {
            7: MagicMock(autospec=FixedDepth),
            3: MagicMock(autospec=FixedDepth),
        }
    }
    with pytest.raises(ValueError):
        _probe = FilterWheelSlotOccupancy(**kwargs)


@pytest.mark.parametrize(
    "invalid_slot_index",
    [
        {},
        [],
        (),
        object(),
        RuntimeError,
        True,
        False,
        math.erfc,
        "",
        "Hello World",
        "Y",
        "+",
        "5",
        "-44",
        None,
        0,
        -8,
        41.2,
        -math.e,
    ]
)
def test_that_error_raised_if_filter_wheel_slot_occupancy_instantiation_lacks_valid_permissions(
    invalid_slot_index: Any
) -> None:
    kwargs = {
        "wheel_name":"w",
        "wheel_capacity": 6,
        "reserved_slot":1,
        "permitted_slots": [2, 4, invalid_slot_index,],
        "occupied_slots": {
            2: MagicMock(autospec=FixedDepth),
            3: MagicMock(autospec=FixedDepth),
        }
    }
    with pytest.raises(ValueError):
        _probe = FilterWheelSlotOccupancy(**kwargs)




