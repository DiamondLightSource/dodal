from typing import Generic, Protocol, TypeVar

import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
from bluesky.callbacks import CallbackBase
from bluesky.utils import MsgGenerator


class FromStr(Protocol):
    def __init__(self, value: str) -> None: ...


T = TypeVar("T", str, int, float)


class _GetRunEngineMetaDataCallback(CallbackBase, Generic[T]):
    def __init__(self, metadata_name: str, expected_datatype: type[T] = str):
        self.metadata: T | None = None
        self.expected_datatype = expected_datatype
        self.metadata_name = metadata_name
        super().__init__()

    def start(self, doc):
        self.metadata = doc.get(self.metadata_name)
        if not self.metadata:
            raise ValueError(
                f"Requested RunEngine metadata '{self.metadata_name}' could not be found"
            )
        try:
            assert self.metadata
            self.metadata = self.expected_datatype(self.metadata)
        except Exception as e:
            raise TypeError(
                f"Requested RunEngine metadata '{self.metadata}' could not be converted to requested type '{self.expected_datatype}'"
            ) from e


def get_run_engine_metadata(
    metadata_name: str, expected_datatype: type[T] = str
) -> MsgGenerator[T]:
    """
    Get metadata stored on the RunEngine.

    Creates a callback and a dummy run event to read metadata from the RunEngine. Useful
    for plans which don't have reference to the RunEngine, for example when running through
    BlueAPI

    Args:
    metadata_name: The string name for requested metadata
    expected_datatype: The datatype you expect the data to be in. String by default.
    """

    callback = _GetRunEngineMetaDataCallback[T](metadata_name, expected_datatype)

    @bpp.subs_decorator(callback)
    @bpp.run_decorator()
    def _trigger_callback() -> MsgGenerator:
        yield from bps.null()

    yield from _trigger_callback()

    assert callback.metadata, "Requested metadata returned as type None"
    return callback.metadata
