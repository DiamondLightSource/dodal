from nslsii.ad33 import CamV33Mixin
from ophyd.areadetector.cam import AreaDetectorCam
from ophyd.areadetector.filestore_mixins import FileStoreHDF5, FileStoreIterativeWrite
from ophyd.areadetector.plugins import HDF5Plugin


class SyncrhonisedAdDriverBase(AreaDetectorCam, CamV33Mixin):
    """
    Base Ophyd device to control an AreaDetector driver and
    syncrhonise it on other AreaDetector plugins, even non-blocking ones.
    """

    def stage(self, *args, **kwargs):
        # Makes the detector allow non-blocking AD plugins but makes Ophyd use
        # the AcquireBusy PV to determine when an acquisition is complete
        self.ensure_nonblocking()
        return super().stage(*args, **kwargs)


class Hdf5Writer(HDF5Plugin, FileStoreHDF5, FileStoreIterativeWrite):
    """ """

    pool_max_buffers = None
    file_number_sync = None
    file_number_write = None

    def get_frames_per_point(self):
        return self.parent.cam.num_images.get()
