from pathlib import Path

from bluesky.run_engine import RunEngine
from bluesky.utils import MsgGenerator
from ophyd_async.core import PathInfo, PathProvider

from dodal.plan_stubs.data_session import attach_data_session_metadata_wrapper


class FakeProvider(PathProvider):
    def __call__(self, device_name: str | None = None) -> PathInfo:
        return PathInfo(Path("/tmp"), "test")


def test_attach_data_session_metadata_wrapper(caplog, RE: RunEngine):
    def fake_plan() -> MsgGenerator[None]:
        yield from []

    path_provider = FakeProvider()
    plan = attach_data_session_metadata_wrapper(
        plan=fake_plan(), provider=path_provider
    )
    RE(plan)

    assert (
        f"{path_provider} is not an UpdatingPathProvider, {attach_data_session_metadata_wrapper.__name__} will have no effect"
        in caplog.text
    )
