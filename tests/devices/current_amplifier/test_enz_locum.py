import pytest
from ophyd_async.core import Signal, init_devices

from dodal.devices.current_amplifiers import EnzLocum


@pytest.fixture
async def locum() -> EnzLocum:
    async with init_devices(mock=True):
        locum = EnzLocum("LOCUM:")
    return locum


def test_locum_uses_prefix_for_pvs(locum: EnzLocum) -> None:
    signals = [signal for _, signal in locum.children() if isinstance(signal, Signal)]
    assert signals
    assert all(
        signal.source.split("://", 1)[-1].startswith("LOCUM:") for signal in signals
    )


async def test_locum_configuration(locum: EnzLocum) -> None:
    config = await locum.describe_configuration()
    assert set(config) == {signal.name for _, signal in locum.children()}
