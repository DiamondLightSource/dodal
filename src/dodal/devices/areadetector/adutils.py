from ophyd import Component as Cpt
from ophyd import EpicsSignal, EpicsSignalRO
from ophyd.areadetector.cam import AreaDetectorCam
from ophyd.areadetector.filestore_mixins import FileStoreHDF5, FileStoreIterativeWrite
from ophyd.areadetector.plugins import HDF5Plugin


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
