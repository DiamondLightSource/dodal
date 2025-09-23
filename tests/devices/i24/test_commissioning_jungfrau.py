import asyncio
from pathlib import Path, PurePath
from unittest.mock import MagicMock

import pytest
from ophyd_async.core import (
    AutoIncrementingPathProvider,
    StaticFilenameProvider,
    TriggerInfo,
    init_devices,
)
from ophyd_async.testing import (
    set_mock_value,
)

from dodal.devices.i24.commissioning_jungfrau import CommissioningJungfrau


@pytest.fixture
def jungfrau(tmpdir: Path) -> CommissioningJungfrau:
    with init_devices(mock=True):
        name = StaticFilenameProvider("jf_out")
        path = AutoIncrementingPathProvider(name, PurePath(tmpdir))
        detector = CommissioningJungfrau("", "", path)

    return detector


async def test_jungfrau_with_temporary_writer(
    jungfrau: CommissioningJungfrau,
):
    set_mock_value(jungfrau._writer.writer_ready, 1)
    set_mock_value(jungfrau._writer.frame_counter, 10)
    jungfrau._writer._path_info = MagicMock()
    await jungfrau.prepare(TriggerInfo(livetime=1e-3, exposures_per_event=5))
    assert await jungfrau._writer.frame_counter.get_value() == 0
    await jungfrau.kickoff()
    status = jungfrau.complete()

    async def _do_fake_writing():
        for frame in range(1, 5):
            set_mock_value(jungfrau._writer.frame_counter, frame)
            assert not status.done
        set_mock_value(jungfrau._writer.frame_counter, 5)

    await asyncio.gather(status, _do_fake_writing())
    jungfrau._writer._path_info.assert_called_once()


def test_collect_stream_docs_raises_error(jungfrau: CommissioningJungfrau):
    with pytest.raises(NotImplementedError):
        jungfrau._writer.collect_stream_docs("jungfrau", 0)
