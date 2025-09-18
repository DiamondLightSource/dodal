from ophyd_async.core import StandardReadable, SubsetEnum
from ophyd_async.epics.core import epics_signal_rw


class FilterMotor(StandardReadable):
    """
    A device representing a filter motor with selectable filter positions.

    Parameters:
        prefix (str): The EPICS PV prefix for the filter motor.
        filter_selections (type[SubsetEnum]): An enumeration type representing the possible filter selections.
        name (str, optional): The name of the device. Defaults to an empty string.

    Attributes:
        user_setpoint: A read-write EPICS signal for selecting the filter position.
    """

    def __init__(
        self, prefix: str, filter_selections: type[SubsetEnum], name: str = ""
    ):
        with self.add_children_as_readables():
            self.user_setpoint = epics_signal_rw(filter_selections, f"{prefix}SELECT")
        super().__init__(name=name)
