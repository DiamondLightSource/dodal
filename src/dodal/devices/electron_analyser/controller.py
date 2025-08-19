from ophyd_async.epics.adcore import ADBaseController, ADBaseIO


class ElectronAnalyserController(ADBaseController[ADBaseIO]):
    """
    Simple controller for driver with no dead time.
    """

    def get_deadtime(self, exposure: float | None) -> float:
        return 0
