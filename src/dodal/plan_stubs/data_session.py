import logging

from bluesky import plan_stubs as bps
from bluesky import preprocessors as bpp
from bluesky.utils import MsgGenerator, make_decorator
from ophyd_async.core import PathProvider

from dodal.common.beamlines.beamline_utils import get_path_provider
from dodal.common.types import UpdatingPathProvider

DATA_SESSION = "data_session"
DATA_GROUPS = "data_groups"


def attach_data_session_metadata_wrapper(
    plan: MsgGenerator, provider: PathProvider | None = None
) -> MsgGenerator:
    """
    Attach data session metadata to the runs within a plan and make it correlate
    with an ophyd-async PathProvider.

    This updates the path provider (which in turn makes a call to to a service
    to figure out which scan number we are using for such a scan), and ensures the
    start document contains the correct data session.

    Args:
        plan: The plan to preprocess
        provider: The path provider that participating detectors are aware of.

    Returns:
        MsgGenerator: A plan

    Yields:
        Iterator[Msg]: Plan messages
    """
    try:
        provider = provider or get_path_provider()
    except NameError:
        provider = None

    if isinstance(provider, UpdatingPathProvider):
        yield from bps.wait_for([provider.update])
        ress = yield from bps.wait_for([provider.data_session])
        data_session = ress[0].result()
        # https://github.com/DiamondLightSource/dodal/issues/452
        # As part of 452, write each dataCollection into their own folder, then can use resource_dir directly
        yield from bpp.inject_md_wrapper(plan, md={DATA_SESSION: data_session})
    elif provider is None:
        logging.warning(
            f"There is no PathProvider set, {attach_data_session_metadata_wrapper.__name__} will have no effect"
        )
        yield from plan
    else:
        logging.warning(
            f"{provider} is not an UpdatingPathProvider, {attach_data_session_metadata_wrapper.__name__} will have no effect"
        )
        yield from plan


attach_data_session_metadata_decorator = make_decorator(
    attach_data_session_metadata_wrapper
)
