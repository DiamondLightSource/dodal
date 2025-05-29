from typing import TypeVar

from ophyd_async.core import StrictEnum

from dodal.devices.positioner import Positioner1D


class _Filters(StrictEnum):
    pass


class I03Filters(_Filters):
    EMPTY = "Empty"
    TWO_HUNDRED = "200um"
    ONE_HUNDRED = "100um"


class I04Filters(_Filters):
    EMPTY = "Empty"
    TWO_HUNDRED = "200um"
    FIFTY = "50um"
    OUT = "Out"


T = TypeVar("T", bound=_Filters)


class DiamondFilter(Positioner1D[T]):
    """
    A filter set that is used to reduce the heat load on the monochromator.

    It has 4 slots that can contain filters of different thickness. Changing the thickness
    signal will move the filter set to select this filter.
    """
