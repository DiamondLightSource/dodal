import math

import pytest

from dodal.common.general_maths.arithmetic_conversions import (
    convert_microns_to_cm,
)

# expected success tests (the 'Happy Path'): All numbers here are arbitrary


@pytest.mark.parametrize("input,result", [(10000.0, 1.0), (1000, 0.1)])
def test_conversion_from_microns_to_centimetres(input, result):
    assert convert_microns_to_cm(input) == pytest.approx(result)


# The inauspicuous path
@pytest.mark.parametrize(
    "bad_input",
    ["a", [], None, math.sin, object()],
)
def test_convert_microns_to_cm_raises_error_with_bad_input(bad_input):
    with pytest.raises(TypeError):
        convert_microns_to_cm(bad_input)
