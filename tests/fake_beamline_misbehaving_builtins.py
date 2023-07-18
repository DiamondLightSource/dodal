from math import hypot, log
from typing import TypedDict

from ophyd.utils import DisconnectedError

"""
    Some builtins (e.g. dict, Exception), types that extend
    them, and aliases for them, do not have signature information.
    PEP-8 recommends being conservative with adding typing information
    to builtins and the core Python library, so this may change slowly.
    This beamline uses some types or constructions that are known to
    cause issue but that could conceivably be used in a beamline file.

    - Importing specific exceptions
    - Importing functions from builtins, including math
    - Aliasing builtins, including dict
    - Defining a class that extends TypedDict (e.g. for parameters)

"""


def not_a_device() -> None:
    """
    Importing DisconnectedError is enough to cause issue, but we
    use it here to prevent linting from removing it from the imports.
    """
    raise DisconnectedError()


def also_not_a_device() -> float:
    """
    log and hypot both do not have signatures.
    Not required to actually be used, importing is enough.
    """
    return log(hypot(0, 0))


a = dict
b = Exception


class B(TypedDict):
    """
    Causes issue only if a class that extends TypedDict exists.
    """

    foo: int
