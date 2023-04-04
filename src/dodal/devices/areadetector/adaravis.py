from ophyd import Component as Cpt
from ophyd import DetectorBase
from ophyd.areadetector.base import ADComponent as Cpt
from ophyd.areadetector.detectors import DetectorBase

from .adutils import Hdf5Writer, SingleTriggerV33, SynchronisedAdDriverBase

_ACQUIRE_BUFFER_PERIOD = 0.2


class AdAravisDetector(SingleTriggerV33, DetectorBase):
    cam: SynchronisedAdDriverBase = Cpt(SynchronisedAdDriverBase, suffix="DET:")
    hdf: Hdf5Writer = Cpt(
        Hdf5Writer,
        suffix="HDF5:",
        root="",
        write_path_template="",
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.hdf.kind = "normal"

        self.stage_sigs = {
            # Get stage to wire up the plugins
            self.hdf.nd_array_port: self.cam.port_name.get(),
            # Reset array counter on stage
            self.cam.array_counter: 0,
            # Set image mode to multiple on stage so we have the option, can still
            # set num_images to 1
            self.cam.image_mode: "Multiple",
            # For now, this Ophyd device does not support hardware
            # triggered scanning, disable on stage
            self.cam.trigger_mode: "Off",
            **self.stage_sigs,  # type: ignore
        }

    def stage(self, *args, **kwargs):
        # We have to manually set the acquire period bcause the EPICS driver
        # doesn't do it for us. If acquire time is a staged signal, we use the
        # stage value to calculate the acquire period, otherwise we perform
        # a caget and use the current acquire time.
        if self.cam.acquire_time in self.stage_sigs:
            acquire_time = self.stage_sigs[self.cam.acquire_time]
        else:
            acquire_time = self.cam.acquire_time.get()
        self.stage_sigs[self.cam.acquire_period] = acquire_time + _ACQUIRE_BUFFER_PERIOD

        # Ensure detector warmed up
        self._prime_hdf()

        # Now calling the super method should set the acquire period
        super(AdAravisDetector, self).stage(*args, **kwargs)

    def _prime_hdf(self) -> None:
        """
        Take a single frame and pipe it through the HDF5 writer plugin
        """

        # TODO: It should be possible to work out when the detector does not need
        # priming, but there are a few complex edge cases
        settings = {
            self.hdf.enable: 1,
            self.hdf.nd_array_port: self.cam.port_name.get(),
            self.cam.array_callbacks: 1,
            self.cam.image_mode: "Single",
            self.cam.trigger_mode: "Off",
            # Take the quickest possible frame
            self.cam.acquire_time: 6.3e-05,
            self.cam.acquire_period: 0.003,
        }
        reset_to = {signal: signal.get() for signal in settings.keys()}
        self.cam.acquire.put_complete = True
        self.cam.acquire.set(0).wait(timeout=10)

        # Apply all settings for acquisition
        for signal, value in settings.items():
            # Ensure that .wait really will wait until the PV is set including its RBV
            signal.put_complete = True
            signal.set(value).wait(timeout=10)

        self.cam.acquire.set(1).wait(timeout=10)

        # Revert settings to previous values
        for signal, value in reversed(reset_to.items()):
            signal.set(value).wait(timeout=10)
