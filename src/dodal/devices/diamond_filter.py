from typing import Generic, TypeVar

from ophyd_async.core import StandardReadable, StrictEnum
from ophyd_async.epics.core import epics_signal_rw
from ophyd_async.epics.motor import Motor


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


class DiamondFilter(StandardReadable, Generic[T]):
    """
    A filter set that is used to reduce the heat load on the monochromator.

    It has 4 slots that can contain filters of different thickness. Changing the thickness
    signal will move the filter set to select this filter.
    """

    def __init__(
        self,
        prefix: str,
        data_type: type[T],
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            self.y_motor = Motor(prefix + "Y")
            self.thickness = epics_signal_rw(data_type, f"{prefix}Y:MP:SELECT")

        super().__init__(name)
