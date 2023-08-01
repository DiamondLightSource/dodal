from unittest.mock import MagicMock

import pytest

from dodal.devices.motors import XYZLimitBundle


def test_given_position_in_limits_then_position_valid_returns_true():
    mock_limits = MagicMock(), MagicMock(), MagicMock()
    bundle = XYZLimitBundle(*mock_limits)
    for mock in mock_limits:
        mock.is_within.return_value = True

    assert bundle.position_valid([0, 0, 0])


@pytest.mark.parametrize(
    "axes",
    [[1], [2], [0, 2], [0, 1, 2]],
)
def test_given_axes_not_in_limits_then_position_valid_returns_false(axes):
    mock_limits = MagicMock(), MagicMock(), MagicMock()
    bundle = XYZLimitBundle(*mock_limits)
    for mock in mock_limits:
        mock.is_within.return_value = True
    for axis in axes:
        mock_limits[axis].is_within.return_value = False

    assert not bundle.position_valid([0, 0, 0])


def test_when_position_valid_called_without_3_vector_the_raises():
    mock_limits = MagicMock(), MagicMock(), MagicMock()
    bundle = XYZLimitBundle(*mock_limits)

    with pytest.raises(ValueError):
        raise bundle.position_valid([0, 0, 0, 0])
