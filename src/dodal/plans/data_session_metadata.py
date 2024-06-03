from bluesky import plan_stubs as bps
from bluesky import preprocessors as bpp
from bluesky.utils import make_decorator
from ophyd_async.core import DirectoryInfo

from dodal.common.beamlines import beamline_utils
from dodal.common.types import MsgGenerator, UpdatingDirectoryProvider

DATA_SESSION = "data_session"
DATA_GROUPS = "data_groups"


def attach_data_session_metadata_wrapper(
    plan: MsgGenerator, provider: UpdatingDirectoryProvider | None = None
) -> MsgGenerator:
    """
    Attach data session metadata to the runs within a plan and make it correlate
    with an ophyd-async DirectoryProvider.

    This updates the directory provider (which in turn makes a call to to a service
    to figure out which scan number we are using for such a scan), and ensures the
    start document contains the correct data session.

    Args:
        plan: The plan to preprocess
        provider: The directory provider that participating detectors are aware of.

    Returns:
        MsgGenerator: A plan

    Yields:
        Iterator[Msg]: Plan messages
    """
    if provider is None:
        provider = beamline_utils.get_directory_provider()
    yield from bps.wait_for([provider.update])
    directory_info: DirectoryInfo = provider()
    # https://github.com/DiamondLightSource/dodal/issues/452
    # As part of 452, write each dataCollection into their own folder, then can use resource_dir directly
    data_session = directory_info.prefix.removesuffix("-")
    yield from bpp.inject_md_wrapper(plan, md={DATA_SESSION: data_session})


attach_data_session_metadata_decorator = make_decorator(
    attach_data_session_metadata_wrapper
)
