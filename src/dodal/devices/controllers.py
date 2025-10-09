from typing import TypeVar

from ophyd_async.epics.adcore import ADBaseController, ADBaseIO, ADImageMode

ADBaseIOT = TypeVar("ADBaseIOT", bound=ADBaseIO)


class ConstantDeadTimeController(ADBaseController[ADBaseIOT]):
    """
    ADBaseController with a configured constant deadtime for a driver of type ADBaseIO.
    """

    def __init__(
        self,
        driver: ADBaseIOT,
        deadtime: float,
        image_mode: ADImageMode = ADImageMode.MULTIPLE,
    ):
        super().__init__(driver, image_mode=image_mode)
        self.deadtime = deadtime

    def get_deadtime(self, exposure: float | None) -> float:
        return self.deadtime
