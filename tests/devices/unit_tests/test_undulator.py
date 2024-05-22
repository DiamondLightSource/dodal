import pytest

from dodal.devices.undulator import Undulator


@pytest.mark.parametrize(
    "key",
    [
        "undulator-gap_motor",
        "undulator-current_gap",
        "undulator-gap_access",
    ],
)
async def test_read_and_describe_includes(
    mock_undulator: Undulator,
    key: str,
):
    description = await mock_undulator.describe()
    reading = await mock_undulator.read()

    assert key in description
    assert key in reading
