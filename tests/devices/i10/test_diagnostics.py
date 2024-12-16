from collections import defaultdict
from unittest.mock import Mock

import pytest
from bluesky.plans import count
from bluesky.run_engine import RunEngine
from ophyd_async.core import (
    DeviceCollector,
)
from ophyd_async.testing import (
    assert_emitted,
    callback_on_mock_put,
    set_mock_value,
)

from dodal.devices.i10.diagnostics import I10CentroidDetector


@pytest.fixture
async def mock_centroid_detector(
    prefix: str = "BLXX-EA-DET-007:",
) -> I10CentroidDetector:
    async with DeviceCollector(mock=True):
        mock_centroid_detector = I10CentroidDetector(prefix)
    assert mock_centroid_detector.name == "mock_centroid_detector"
    return mock_centroid_detector


async def test_single_stat_ad(
    mock_centroid_detector: I10CentroidDetector,
    RE: RunEngine,
):
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    num_cnt = 10

    x_mocks = Mock()
    x_mocks.get.side_effect = range(0, 100, 2)

    callback_on_mock_put(
        mock_centroid_detector.drv.acquire,
        lambda *_, **__: set_mock_value(
            mock_centroid_detector.drv.centroid_x, x_mocks.get()
        ),
    )
    RE(count([mock_centroid_detector], num_cnt), capture_emitted)

    drv = mock_centroid_detector.drv
    assert 1 == await drv.acquire.get_value()
    assert True is await drv.wait_for_plugins.get_value()

    assert_emitted(docs, start=1, descriptor=1, event=num_cnt, stop=1)

    assert (
        docs["descriptor"][0]["configuration"]["mock_centroid_detector"]["data"][
            "mock_centroid_detector-drv-acquire_time"
        ]
        == 0
    )
    assert docs["event"][0]["data"]["mock_centroid_detector-drv-array_counter"] == 0

    for i, x in enumerate(range(0, num_cnt, 2)):
        assert docs["event"][i]["data"]["mock_centroid_detector-drv-centroid_x"] == x
