import time as ttime

from ophyd import Component as Cpt
from ophyd import EpicsSignal, EpicsSignalRO, Staged
from ophyd.areadetector import ADTriggerStatus, TriggerBase
from ophyd.areadetector.cam import AreaDetectorCam
from ophyd.areadetector.filestore_mixins import FileStoreHDF5, FileStoreIterativeWrite
from ophyd.areadetector.plugins import HDF5Plugin


class SingleTriggerV33(TriggerBase):
    _status_type = ADTriggerStatus

    def __init__(self, *args, image_name=None, **kwargs):
        super().__init__(*args, **kwargs)
        if image_name is None:
            image_name = "_".join([self.name, "image"])
        self._image_name = image_name

    def trigger(self):
        "Trigger one acquisition."
        if self._staged != Staged.yes:
            raise RuntimeError(
                "This detector is not ready to trigger."
                "Call the stage() method before triggering."
            )

        self._status = self._status_type(self)

        def _acq_done(*args, **kwargs):
            # TODO sort out if anything useful in here
            self._status._finished()

        self._acquisition_signal.put(1, use_complete=True, callback=_acq_done)
        self.dispatch(self._image_name, ttime.time())
        return self._status


class SynchronisedAdDriverBase(AreaDetectorCam):
    """
    Base Ophyd device to control an AreaDetector driver and
    syncrhonise it on other AreaDetector plugins, even non-blocking ones.
    """

    adcore_version = Cpt(EpicsSignalRO, "ADCoreVersion_RBV", string=True, kind="config")
    driver_version = Cpt(EpicsSignalRO, "DriverVersion_RBV", string=True, kind="config")
    wait_for_plugins = Cpt(EpicsSignal, "WaitForPlugins", string=True, kind="config")

    def stage(self, *args, **kwargs):
        # Makes the detector allow non-blocking AD plugins but makes Ophyd use
        # the AcquireBusy PV to determine when an acquisition is complete
        self.ensure_nonblocking()
        return super().stage(*args, **kwargs)

    def ensure_nonblocking(self):
        self.stage_sigs["wait_for_plugins"] = "Yes"
        for c in self.parent.component_names:
            cpt = getattr(self.parent, c)
            if cpt is self:
                continue
            if hasattr(cpt, "ensure_nonblocking"):
                cpt.ensure_nonblocking()


class Hdf5Writer(HDF5Plugin, FileStoreHDF5, FileStoreIterativeWrite):
    """ """

    pool_max_buffers = None
    file_number_sync = None
    file_number_write = None

    def get_frames_per_point(self):
        return self.parent.cam.num_images.get()
