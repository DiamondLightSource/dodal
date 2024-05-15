import importlib.util
import os
from pathlib import Path
from typing import Iterable

# Where beamline names (per the ${BEAMLINE} environment variable don't always
# match up, we have to map between them bidirectionally). The most common use case is
# beamlines with a "-"" in the name such as "i04-1", which is not valid in a Python
# module name. Add any new beamlines whose name differs from their module name to this
# dictionary, which maps ${BEAMLINE} to dodal.beamlines.<MODULE NAME>
_BEAMLINE_NAME_OVERRIDES = {
    "i04-1": "i04_1",
    "i20-1": "i20_1",
}
_MODULE_NAME_OVERRIDES = {
    beamline: module for module, beamline in _BEAMLINE_NAME_OVERRIDES.items()
}


def all_beamline_modules() -> Iterable[str]:
    """
    Get the names of all importable modules in beamlines

    Returns:
        Iterable[str]: Generator of beamline module names
    """
    spec = importlib.util.find_spec(__name__)
    if spec is not None:
        search_paths = [Path(path) for path in spec.submodule_search_locations]
        for path in search_paths:
            for subpath in path.glob("**/*"):
                if subpath.name.endswith(".py") and subpath.name != "__init__.py":
                    yield subpath.with_suffix("").name
    else:
        raise KeyError(f"Unable to find {__name__} module")


def all_beamline_names() -> Iterable[str]:
    """
    Get the names of all beamlines as per the ${BEAMLINE} environment variable

    Returns:
        Iterable[str]: Generator of beamline names that dodal supports
    """
    for module_name in all_beamline_modules():
        yield _MODULE_NAME_OVERRIDES.get(module_name, module_name)


def module_name_for_beamline(beamline: str) -> str:
    """
    Get the module name for a particular beamline, it may differ from the beamline
    name e.g. i04-1 -> i04_1

    Args:
        beamline: The beamline name as per the ${BEAMLINE} environment variable

    Returns:
        str: The importable module name
    """

    return _BEAMLINE_NAME_OVERRIDES.get(beamline, beamline)
