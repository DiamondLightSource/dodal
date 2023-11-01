import tempfile
from typing import Optional

from ophyd_async.core import DirectoryProvider, StaticDirectoryProvider

_SINGLETON: Optional[DirectoryProvider] = None


def set_directory_provider_singleton(provider: DirectoryProvider):
    global _SINGLETON

    _SINGLETON = provider


def get_directory_provider() -> DirectoryProvider:
    if _SINGLETON is not None:
        return _SINGLETON
    else:
        return StaticDirectoryProvider(tempfile.NamedTemporaryFile().name, "")
