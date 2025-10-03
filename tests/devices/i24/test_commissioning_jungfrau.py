import asyncio
from pathlib import Path, PurePath
from unittest.mock import MagicMock

import pytest
from ophyd_async.core import (
    AutoIncrementingPathProvider,
    StaticFilenameProvider,
    StaticPathProvider,
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
    trigger_info = TriggerInfo(livetime=1e-3, exposures_per_event=5)
    await jungfrau.prepare(trigger_info)
    assert await jungfrau._writer.frame_counter.get_value() == 0
    assert (
        await jungfrau._writer.expected_frames.get_value()
        == trigger_info.total_number_of_exposures
    )
    await jungfrau.kickoff()
    status = jungfrau.complete()

    async def _do_fake_writing():
        for frame in range(1, 5):
            set_mock_value(jungfrau._writer.frame_counter, frame)
            assert not status.done
        set_mock_value(jungfrau._writer.frame_counter, 5)

    await asyncio.gather(status, _do_fake_writing())
    jungfrau._writer._path_info.assert_called_once()


async def test_jungfrau_error_when_writing_to_existing_file(tmp_path: Path):
    file_name = "test_file"
    empty_file = tmp_path / file_name
    empty_file.touch()
    name = StaticFilenameProvider(file_name)
    path = StaticPathProvider(name, PurePath(tmp_path))
    with init_devices(mock=True):
        jungfrau = CommissioningJungfrau("", "", path)
    set_mock_value(jungfrau._writer.writer_ready, 1)
    with pytest.raises(FileExistsError):
        await jungfrau.prepare(TriggerInfo(livetime=1e-3, exposures_per_event=5))


def test_collect_stream_docs_raises_error(jungfrau: CommissioningJungfrau):
    with pytest.raises(NotImplementedError):
        jungfrau._writer.collect_stream_docs("jungfrau", 0)
