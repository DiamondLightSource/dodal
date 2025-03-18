from bluesky.run_engine import RunEngine
from bluesky.utils import MsgGenerator

from dodal.common.visit import StartDocumentBasedPathProvider
from dodal.plan_stubs.data_session import attach_data_session_metadata_wrapper


def test_attach_data_session_metadata_wrapper(caplog, RE: RunEngine):

    def fake_plan() -> MsgGenerator[None]:
        yield from []

    path_provider = StartDocumentBasedPathProvider()
    plan = attach_data_session_metadata_wrapper(plan = fake_plan(), provider = path_provider)
    RE(plan)

    assert f"{path_provider} is not an UpdatingPathProvider, {attach_data_session_metadata_wrapper.__name__} will have no effect" in caplog.text
