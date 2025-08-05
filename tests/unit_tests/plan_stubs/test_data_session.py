from unittest.mock import Mock

from bluesky.run_engine import RunEngine
from bluesky.utils import MsgGenerator

from dodal.common.beamlines.beamline_utils import clear_path_provider
from dodal.plan_stubs.data_session import attach_data_session_metadata_wrapper


def test_attach_data_session_metadata_wrapper(caplog, RE: RunEngine):
    def fake_plan() -> MsgGenerator[None]:
        yield from []

    path_provider = Mock()
    plan = attach_data_session_metadata_wrapper(
        plan=fake_plan(), provider=path_provider
    )
    RE(plan)

    assert (
        f"{path_provider} is not an UpdatingPathProvider, {attach_data_session_metadata_wrapper.__name__} will have no effect"
        in caplog.text
    )


def test_attach_data_session_metadata_wrapper_with_no_provider_is_noop(
    caplog, RE: RunEngine
):
    def fake_plan() -> MsgGenerator[None]:
        yield from []

    clear_path_provider()
    plan = attach_data_session_metadata_wrapper(plan=fake_plan())
    RE(plan)

    assert f"There is no PathProvider set, {attach_data_session_metadata_wrapper.__name__} will have no effect"
