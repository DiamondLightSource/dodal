import math

import pytest

from dodal.common.general_maths.arithmetic_conversions import (
    convert_ev_to_kev,
)

# expected success tests (the 'Happy Path'): All numbers here are arbitrary


@pytest.mark.parametrize("input,result", [(1000, 1.0), (100, 0.1)])
def test_conversion_from_electronvolts_to_kiloelectronvolts(input, result):
    assert convert_ev_to_kev(input) == pytest.approx(result)


# The inauspicuous path
@pytest.mark.parametrize(
    "bad_input",
    ["a", [], None, math.sin, object()],
)
def test_convert_ev_to_kev_raises_error_with_bad_input(bad_input):
    with pytest.raises(TypeError):
        convert_ev_to_kev(bad_input)
