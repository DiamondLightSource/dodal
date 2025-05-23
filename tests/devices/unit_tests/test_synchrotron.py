import json
from collections.abc import Awaitable, Callable
from typing import Any

import bluesky.plan_stubs as bps
import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import StandardReadable, init_devices
from ophyd_async.testing import set_mock_value

from dodal.devices.synchrotron import (
    Synchrotron,
    SynchrotronMode,
)

CURRENT = 0.556677
USER_COUNTDOWN = 55.0
START_COUNTDOWN = 66.0
END_COUNTDOWN = 77.0
ENERGY = 3.0158
MODE = SynchrotronMode.INJECTION
PROBE = "x-ray"
TYPE = "Synchrotron X-ray Source"
NUMBER = "number"
STRING = "string"
EMPTY_LIST: list = []

READINGS = [CURRENT, ENERGY]
CONFIGS = [PROBE, MODE.value, TYPE]

READING_FIELDS = ["value", "alarm_severity"]
DESCRIPTION_FIELDS = ["source", "dtype", "shape"]
READING_ADDRESSES = [
    "mock+ca://SR-DI-DCCT-01:SIGNAL",
    "mock+ca://CS-CS-MSTAT-01:BEAMENERGY",
]

CONFIG_ADDRESSES = [
    "mock+soft://synchrotron-probe",
    "mock+ca://CS-CS-MSTAT-01:MODE",
    "mock+soft://synchrotron-type",
]

READ_SIGNALS = [
    "synchrotron-current",
    "synchrotron-energy",
]

CONFIG_SIGNALS = [
    "synchrotron-probe",
    "synchrotron-synchrotron_mode",
    "synchrotron-type",
]

EXPECTED_READ_RESULT = f"""{{
  "{READ_SIGNALS[0]}": {{
    "{READING_FIELDS[0]}": {READINGS[0]},
    "{READING_FIELDS[1]}": 0
  }},
  "{READ_SIGNALS[1]}": {{
    "{READING_FIELDS[0]}": {READINGS[1]},
    "{READING_FIELDS[1]}": 0
  }}
}}"""

EXPECTED_READ_CONFIG_RESULT = f"""{{
  "{CONFIG_SIGNALS[0]}":{{
    "{READING_FIELDS[0]}": "{CONFIGS[0]}",
    "{READING_FIELDS[1]}": 0
  }},
  "{CONFIG_SIGNALS[1]}":{{
    "{READING_FIELDS[0]}": "{CONFIGS[1]}",
    "{READING_FIELDS[1]}": 0
  }},
  "{CONFIG_SIGNALS[2]}":{{
    "{READING_FIELDS[0]}": "{CONFIGS[2]}",
    "{READING_FIELDS[1]}": 0
  }}
}}"""

EXPECTED_DESCRIBE_RESULT = f"""{{
  "{READ_SIGNALS[0]}":{{
    "{DESCRIPTION_FIELDS[0]}": "{READING_ADDRESSES[0]}",
    "{DESCRIPTION_FIELDS[1]}": "{NUMBER}",
    "{DESCRIPTION_FIELDS[2]}": {EMPTY_LIST}
  }},
  "{READ_SIGNALS[1]}":{{
    "{DESCRIPTION_FIELDS[0]}": "{READING_ADDRESSES[1]}",
    "{DESCRIPTION_FIELDS[1]}": "{NUMBER}",
    "{DESCRIPTION_FIELDS[2]}": {EMPTY_LIST}
  }}
}}"""

EXPECTED_DESCRIBE_CONFIG_RESULT = f"""{{
  "{CONFIG_SIGNALS[0]}":{{
    "{DESCRIPTION_FIELDS[0]}": "{CONFIG_ADDRESSES[0]}",
    "{DESCRIPTION_FIELDS[1]}": "{STRING}",
    "{DESCRIPTION_FIELDS[2]}": {EMPTY_LIST}
  }},
  "{CONFIG_SIGNALS[1]}":{{
    "{DESCRIPTION_FIELDS[0]}": "{CONFIG_ADDRESSES[1]}",
    "{DESCRIPTION_FIELDS[1]}": "{STRING}",
    "{DESCRIPTION_FIELDS[2]}": {EMPTY_LIST}
  }},
  "{CONFIG_SIGNALS[2]}":{{
    "{DESCRIPTION_FIELDS[0]}": "{CONFIG_ADDRESSES[2]}",
    "{DESCRIPTION_FIELDS[1]}": "{STRING}",
    "{DESCRIPTION_FIELDS[2]}": {EMPTY_LIST}
  }}
}}"""


@pytest.fixture
async def sim_synchrotron() -> Synchrotron:
    async with init_devices(mock=True):
        sim_synchrotron = Synchrotron()
    set_mock_value(sim_synchrotron.current, CURRENT)
    set_mock_value(sim_synchrotron.machine_user_countdown, USER_COUNTDOWN)
    set_mock_value(sim_synchrotron.top_up_start_countdown, START_COUNTDOWN)
    set_mock_value(sim_synchrotron.top_up_end_countdown, END_COUNTDOWN)
    set_mock_value(sim_synchrotron.energy, ENERGY)
    set_mock_value(sim_synchrotron.synchrotron_mode, MODE)
    return sim_synchrotron


async def test_synchrotron_read(sim_synchrotron: Synchrotron):
    await verify(
        sim_synchrotron.read,
        READ_SIGNALS,
        READING_FIELDS,
        EXPECTED_READ_RESULT,
    )


async def test_synchrotron_read_configuration(sim_synchrotron: Synchrotron):
    await verify(
        sim_synchrotron.read_configuration,
        CONFIG_SIGNALS,
        READING_FIELDS,
        EXPECTED_READ_CONFIG_RESULT,
    )


async def test_synchrotron_describe(sim_synchrotron: Synchrotron):
    await verify(
        sim_synchrotron.describe,
        READ_SIGNALS,
        DESCRIPTION_FIELDS,
        EXPECTED_DESCRIBE_RESULT,
    )


async def test_synchrotron_describe_configuration(sim_synchrotron: Synchrotron):
    await verify(
        sim_synchrotron.describe_configuration,
        CONFIG_SIGNALS,
        DESCRIPTION_FIELDS,
        EXPECTED_DESCRIBE_CONFIG_RESULT,
    )


async def test_synchrotron_count(RE: RunEngine, sim_synchrotron: Synchrotron):
    docs = []
    RE(count_sim(sim_synchrotron), lambda x, y: docs.append(y))

    assert len(docs) == 4
    assert sim_synchrotron.name in docs[1]["configuration"]
    cfg_data_keys = docs[1]["configuration"][sim_synchrotron.name]["data_keys"]
    for sig, addr in zip(CONFIG_SIGNALS, CONFIG_ADDRESSES, strict=False):
        assert sig in cfg_data_keys
        assert cfg_data_keys[sig][DESCRIPTION_FIELDS[0]] == addr
        assert cfg_data_keys[sig][DESCRIPTION_FIELDS[1]] == STRING
        assert cfg_data_keys[sig][DESCRIPTION_FIELDS[2]] == EMPTY_LIST
    cfg_data = docs[1]["configuration"][sim_synchrotron.name]["data"]
    for sig, value in zip(CONFIG_SIGNALS, CONFIGS, strict=False):
        assert cfg_data[sig] == value
    data_keys = docs[1]["data_keys"]
    for sig, addr in zip(READ_SIGNALS, READING_ADDRESSES, strict=False):
        assert sig in data_keys
        assert data_keys[sig][DESCRIPTION_FIELDS[0]] == addr
        assert data_keys[sig][DESCRIPTION_FIELDS[1]] == NUMBER
        assert data_keys[sig][DESCRIPTION_FIELDS[2]] == EMPTY_LIST

    data = docs[2]["data"]
    assert len(data) == len(READ_SIGNALS)
    for sig, value in zip(READ_SIGNALS, READINGS, strict=False):
        assert sig in data
        assert data[sig] == value


async def verify(
    func: Callable[[], Awaitable[dict[str, Any]]],
    signals: list[str],
    fields: list[str],
    expectation: str,
):
    expected = json.loads(expectation)
    result = await func()

    for signal in signals:
        for field in fields:
            assert result[signal][field] == expected[signal][field]


def count_sim(det: StandardReadable, times: int = 1):
    """Test plan to do equivalent of bp.count for a sim detector (no file writing)."""

    yield from bps.stage_all(det)
    yield from bps.open_run()
    yield from bps.declare_stream(det, name="primary", collect=False)
    for _ in range(times):
        yield from bps.wait(group="wait_for_trigger")
        yield from bps.create()
        yield from bps.read(det)
        yield from bps.save()

    yield from bps.close_run()
    yield from bps.unstage_all(det)
