import importlib.util
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Mapping

# Where beamline names (per the ${BEAMLINE} environment variable don't always
# match up, we have to map between them bidirectionally). The most common use case is
# beamlines with a "-"" in the name such as "i04-1", which is not valid in a Python
# module name. Add any new beamlines whose name differs from their module name to this
# dictionary, which maps ${BEAMLINE} to dodal.beamlines.<MODULE NAME>
_BEAMLINE_NAME_OVERRIDES = {
    "i04-1": "i04_1",
    "i20-1": "i20_1",
    "s03": "i03",
}


def all_beamline_modules() -> Iterable[str]:
    """
    Get the names of all importable modules in beamlines

    Returns:
        Iterable[str]: Generator of beamline module names
    """

    # This is done by inspecting file names rather than modules to avoid
    # premature importing
    spec = importlib.util.find_spec(__name__)
    if spec is not None:
        search_paths = [Path(path) for path in spec.submodule_search_locations]
        for path in search_paths:
            for subpath in path.glob("**/*"):
                if (
                    subpath.name.endswith(".py")
                    and subpath.name != "__init__.py"
                    and ("__pycache__" not in str(subpath))
                ):
                    yield subpath.with_suffix("").name
    else:
        raise KeyError(f"Unable to find {__name__} module")


def all_beamline_names() -> Iterable[str]:
    """
    Get the names of all beamlines as per the ${BEAMLINE} environment variable

    Returns:
        Iterable[str]: Generator of beamline names that dodal supports
    """
    inverse_mapping = _module_name_overrides()
    for module_name in all_beamline_modules():
        yield from inverse_mapping.get(module_name, set()).union({module_name})


@lru_cache
def _module_name_overrides() -> Mapping[str, set[str]]:
    """
    Get the inverse of _BEAMLINE_NAME_OVERRIDES so that modules can be mapped back to
    beamlines. _BEAMLINE_NAME_OVERRIDES is expected to be a constant so the return
    value is cached.

    Returns:
        Mapping[str, set[str]]: A dictionary mapping the name of a dodal module to the
        set of beamlines it supports.
    """

    inverse_mapping: dict[str, set[str]] = {}
    for beamline, module in _BEAMLINE_NAME_OVERRIDES.items():
        inverse_mapping[module] = inverse_mapping.get(module, set()).union({beamline})
    return inverse_mapping


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
