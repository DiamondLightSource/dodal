from typing import TypeVar

from ophyd_async.core import StrictEnum


class SelectedSource(StrictEnum):
    SOURCE1 = "source1"
    SOURCE2 = "source2"


T = TypeVar("T")


def get_obj_from_selected_source(selected_source: SelectedSource, s1: T, s2: T) -> T:
    """Util function that maps enum values for SelectedSource to two objects. It then
    returns one of the objects that corrosponds to the selected_source value.
    """
    match selected_source:
        case SelectedSource.SOURCE1:
            return s1
        case SelectedSource.SOURCE2:
            return s2
