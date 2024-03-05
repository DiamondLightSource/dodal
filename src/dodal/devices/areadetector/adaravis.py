import asyncio
from enum import Enum
from typing import Any, Dict, Mapping, Optional

from bluesky.protocols import HasHints, Hints
from ophyd import Component as Cpt
from ophyd import DetectorBase, EpicsSignal, Signal
from ophyd.areadetector.base import ADComponent as Cpt
from ophyd.areadetector.detectors import DetectorBase
from ophyd_async.core import (
    AsyncStatus,
    DetectorControl,
    DetectorTrigger,
    DirectoryProvider,
    StandardDetector,
    set_and_wait_for_value,
)
from ophyd_async.epics.areadetector.drivers import ADBase, ADBaseShapeProvider
from ophyd_async.epics.areadetector.utils import ImageMode, ad_rw, stop_busy_record
from ophyd_async.epics.areadetector.writers import HDFWriter, NDFileHDF, NDPluginStats

from .adutils import Hdf5Writer, SingleTriggerV33, SynchronisedAdDriverBase

_ACQUIRE_BUFFER_PERIOD = 0.2


class AdAravisDetector(SingleTriggerV33, DetectorBase):
    """
    Ophyd implementation of the AdAravis detector.
    """

    cam = Cpt(SynchronisedAdDriverBase, suffix="DET:")
    hdf = Cpt(
        Hdf5Writer,
        suffix="HDF5:",
        root="",
        write_path_template="",
    )
    _priming_settings: Mapping[Signal, Any]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.hdf.kind = "normal"

        # Values for staging
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

        # Settings to apply when priming plugins during pre-stage
        self._priming_settings = {
            self.hdf.enable: 1,
            self.hdf.nd_array_port: self.cam.port_name.get(),
            self.cam.array_callbacks: 1,
            self.cam.image_mode: "Single",
            self.cam.trigger_mode: "Off",
            # Take the quickest possible frame
            self.cam.acquire_time: 6.3e-05,
            self.cam.acquire_period: 0.003,
        }

        # Signals that control driver and hdf writer should be put_complete to
        # avoid race conditions during priming
        for signal in set(self.stage_sigs.keys()).union(
            set(self._priming_settings.keys())
        ):
            if isinstance(signal, EpicsSignal):
                signal.put_complete = True
        self.cam.acquire.put_complete = True

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

        # Backup state and ensure we are not acquiring
        reset_to = {signal: signal.get() for signal in self._priming_settings.keys()}
        self.cam.acquire.set(0).wait(timeout=10)

        # Apply all settings for acquisition
        for signal, value in self._priming_settings.items():
            # Ensure that .wait really will wait until the PV is set including its RBV
            signal.set(value).wait(timeout=10)

        # Acquire a frame
        self.cam.acquire.set(1).wait(timeout=10)

        # Revert settings to previous values
        for signal, value in reversed(reset_to.items()):
            signal.set(value).wait(timeout=10)


class TriggerSourceMako(str, Enum):
    freerun = "Freerun"
    line_1 = "Line1"
    line_2 = "Line2"
    fixed_rate = "FixedRate"
    software = "Software"
    # action_0 = "Action0"
    # action_1 = "Action1"


class TriggerModeMako(str, Enum):
    on = "On"
    off = "Off"


class AdAravisMakoDriver(ADBase):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.trigger_mode = ad_rw(TriggerModeMako, prefix + "TriggerMode")
        self.trigger_source = ad_rw(TriggerSourceMako, prefix + "TriggerSource")
        super().__init__(prefix, name=name)


class AdAravisMakoController(DetectorControl):
    # TODO: Extract this to config and actually use the model of the camera.
    # https://github.com/DiamondLightSource/dodal/issues/340
    # cite: https://cdn.alliedvision.com/fileadmin/content/documents/products/cameras/various/appnote/GigE/GigE-Cameras_AppNote_PIV-Min-Time-Between-Exposures.pdf
    _deadtime_map: Dict[str, float] = {
        "GB650": 78.0e-6,
        "GC650": 121e-6,
        "GE680": 38.2e-6,
        "GT1290": 90e-6,
        "GX1050": 19.9e-6,
        "G-031": 15e-6,
        "G-030": 96e-6,
        "GB660": 75.0e-6,
        "GC655": 121e-6,
        "GE1050": 134e-6,
        "GT1380": 80e-6,
        "GX1660": 19.6e-6,
        "G-032": 283e-6,
        # "G-032": 74e-6,  # Duplicated key, ignoring lower
        "GB1380": 80.0e-6,
        "GC660": 75.0e-6,
        "GE1650": 104e-6,
        "GT1600": 64e-6,
        "GX1910": 19.9e-6,
        "G-033": 93e-6,
        "G-125": 70e-6,
        # "G-125": 63e-6,  # Duplicated key, ignoring lower
        "GB2450": 20.8e-6,
        "GC750": 91.0e-6,
        "GE1660": 62.1e-6,
        "GT1660": 23.6e-6,
        "GX1920": 50.0e-6,
        "G-046": 114e-6,
        "G-131": 24e-6,
        "GC780": 113e-6,
        "GE1900": 113e-6,
        "GT1910": 26e-6,
        "GX2300": 21.4e-6,
        "G-192": 34e-6,
        "GC1020": 123e-6,
        "GE1910": 71.0e-6,
        "GT1920": 52e-6,
        "G-145": 106e-6,
        "G-223": 84e-6,
        # "G-223": 69e-6,  # Duplicated key, ignoring lower
        "GC1290": 89.8e-6,
        "GE2040": 115e-6,
        "GT1930": 196e-6,
        "GX3300": 22.2e-6,
        "G-234": 269e-6,
        "GC1350": 107e-6,
        "GE4000": 110e-6,
        "GT1930L": 196e-6,
        "GX6600": 44.0e-6,
        "G-146": 88e-6,
        "G-419": 130e-6,
        # "G-419": 107e-6,  # Duplicated key, ignoring lower
        "GC1380": 125e-6,
        "GE4900": 110e-6,
        "GT2000": 76e-6,
        "G-201": 60e-6,
        "G-503": 451e-6,
        "GC1380H": 84.0e-6,
        "GT2050": 116e-6,
        "GC1600": 115e-6,
        "GT2300": 25e-6,
        "GC1600H": 60.0e-6,
        "GT2450": 24.8e-6,
        "G-235": 210e-6,
        "GC2450": 20.8e-6,
        "GT2750": 55e-6,
        "G-282": 47e-6,
        "GT3300": 29e-6,
        "G-283": 47e-6,
        "GT3400": 54e-6,
        "GT4907": 56e-6,
        "G-504": 29e-6,
        "GT6600": 48e-6,
        "G-505": 76e-6,
        "G-609": 47e-6,
        "G-917": 47e-6,
        "G-145-30fps": 35e-6,
        "G-201-30fps": 72e-6,
        "GX2750": float("nan"),
    }

    def __init__(self, driver: AdAravisMakoDriver, gpio_number: int) -> None:
        self.driver = driver

        self.gpio_number = gpio_number
        assert gpio_number in {1, 2}, "invalid gpio number"
        self.TRIGGER_SOURCE = {
            DetectorTrigger.internal: TriggerSourceMako.fixed_rate,
            DetectorTrigger.constant_gate: TriggerSourceMako[
                f"line_{self.gpio_number}"
            ],
            DetectorTrigger.edge_trigger: TriggerSourceMako[f"line_{self.gpio_number}"],
        }

    def get_deadtime(self, exposure: float) -> float:
        # https://github.com/DiamondLightSource/dodal/issues/340
        return self._deadtime_map.get("G-234")

    async def arm(
        self,
        trigger: DetectorTrigger = DetectorTrigger.internal,
        num: int = 0,
        exposure: Optional[float] = None,
    ) -> AsyncStatus:
        if num == 0:
            image_mode = ImageMode.continuous
        else:
            image_mode = ImageMode.multiple
        if exposure is not None:
            await self.driver.acquire_time.set(exposure)

        # trigger mode must be set first and on it's own!
        await self.driver.trigger_mode.set(TriggerModeMako.on)

        await asyncio.gather(
            self.driver.trigger_source.set(self.TRIGGER_SOURCE[trigger]),
            self.driver.num_images.set(num),
            self.driver.image_mode.set(image_mode),
        )

        status = await set_and_wait_for_value(self.driver.acquire, True)
        return status

    async def disarm(self):
        await stop_busy_record(self.driver.acquire, False, timeout=1)


class SumHDFAravisDetector(StandardDetector, HasHints):
    """
    Ophyd-async implementation of the AdAravisDetector
    """

    def __init__(
        self,
        name: str,
        prefix: str,
        directory_provider: DirectoryProvider,
        gpio_number: int = 1,
    ):
        drv = AdAravisMakoDriver(prefix + "DET:")
        hdf = NDFileHDF(prefix + "HDF5:")

        self.drv = drv
        self.hdf = hdf
        self.stats = NDPluginStats(prefix + "STAT:")

        super().__init__(
            AdAravisMakoController(drv, gpio_number=gpio_number),
            HDFWriter(
                hdf,
                directory_provider,
                lambda: self.name,
                ADBaseShapeProvider(drv),
                sum="StatsTotal",
                temp="Temperature",
            ),
            config_sigs=[drv.acquire_time, drv.acquire],
            name=name,
        )

    @property
    def hints(self) -> Hints:
        return self.writer.hints
