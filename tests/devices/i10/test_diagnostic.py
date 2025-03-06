import pickle
from collections import defaultdict
from pathlib import Path
from unittest import mock
from unittest.mock import Mock

import numpy as np
import pytest
from bluesky.plans import scan
from bluesky.run_engine import RunEngine
from numpy import poly1d
from ophyd_async.core import init_devices
from ophyd_async.testing import (
    assert_emitted,
    callback_on_mock_put,
    get_mock_put,
    set_mock_value,
)

from dodal.devices.apple2_undulator import (
    UndulatorGap,
    UndulatorGateStatus,
    UndulatorJawPhase,
    UndulatorPhaseAxes,
)
from dodal.devices.i10.diagnostics import D3Position, D5APosition, Positioner
from dodal.devices.i10.i10_apple2 import (
    DEFAULT_JAW_PHASE_POLY_PARAMS,
    I10Apple2,
    I10Apple2PGM,
    I10Apple2Pol,
    LinearArbitraryAngle,
    convert_csv_to_lookup,
)


@pytest.fixture
async def mock_positioner(prefix: str = "BLXX-EA-007:") -> Positioner:
    async with init_devices(mock=True):
        mock_positioner = Positioner(prefix, positioner_enum=D3Position)
    assert mock_positioner.name == "mock_positioner"
    return mock_positioner


async def test_positioner_fail_wrong_value(mock_positioner: Positioner):
    with pytest.raises(ValueError):
        await mock_positioner.set(D5APosition.LA)


async def test_positioner_set_success(mock_positioner: Positioner):
    await mock_positioner.set(D3Position.GRID)
    get_mock_put(mock_positioner.stage_position).assert_awaited_once_with(
        D3Position.GRID, wait=True
    )
