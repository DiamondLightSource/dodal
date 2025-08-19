from typing import TypeVar

from ophyd_async.epics.adcore import (
    ADBaseController,
    ADBaseIO,
)

ADBaseIOT = TypeVar("ADBaseIOT", bound=ADBaseIO)


class ConstantDeadTimeController(ADBaseController[ADBaseIOT]):
    """
    Controller for a driver with a configured constant deadtime.
    """

    def __init__(self, driver: ADBaseIOT, deadtime: float):
        super().__init__(driver)
        self.deadtime = deadtime

    def get_deadtime(self, exposure: float | None) -> float:
        return self.deadtime
