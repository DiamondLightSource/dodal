from dataclasses import dataclass, fields
from typing import Dict

from bluesky.protocols import Reading
from event_model.documents.event_descriptor import DataKey
from ophyd_async.core import DirectoryProvider, merge_gathered_dicts
from ophyd_async.epics.areadetector import AravisDetector, PilatusDetector
from ophyd_async.epics.areadetector.aravis import AravisController

ValueAndUnits = tuple[float, str]


@dataclass
class MetadataHolder:
    # TODO: just in case this is useful more widely...
    async def describe(self, parent_name: str) -> Dict[str, DataKey]:
        def datakey(value) -> DataKey:
            if isinstance(value, tuple):
                return {"units": value[1], **datakey(value[0])}
            dtype = "string"
            shape = []
            match value:
                case bool():
                    dtype = "boolean"
                case int():
                    dtype = "integer"
                case float():
                    dtype = "number"
                case str():
                    dtype = "string"
                case list():
                    dtype = "array"
                    shape = [len(value)]

            return {"dtype": dtype, "shape": shape, "source": "calibration"}

        return {
            f"{parent_name}-{field.name}": datakey(getattr(self, field.name))
            for field in fields(self)
            if getattr(self, field.name, None) is not None
        }

    async def read(self, parent_name: str) -> Dict[str, Reading]:
        def reading(value):
            if isinstance(value, tuple):
                return reading(value[0])
            return {"timestamp": -1, "value": value}

        return {
            f"{parent_name}-{field.name}": reading(getattr(self, field.name))
            for field in fields(self)
            if getattr(self, field.name, None) is not None
        }


@dataclass
class NXSasMetadataHolder(MetadataHolder):
    """
    Required fields for NXDetectors that are used in an NXsas application definition.
    All fields are Configuration and read once per run only.
    """

    distance: ValueAndUnits
    x_pixel_size: ValueAndUnits
    y_pixel_size: ValueAndUnits
    beam_center_x: ValueAndUnits | None = None
    beam_center_y: ValueAndUnits | None = None
    aequetorial_angle: ValueAndUnits | None = None
    azimuthal_angle: ValueAndUnits | None = None
    polar_angle: ValueAndUnits | None = None
    rotation_angle: ValueAndUnits | None = None
    threshold_energy: ValueAndUnits | None = None
    serial_number: str | None = None
    sensor_material: str | None = None
    sensor_thickness: ValueAndUnits | None = None
    description: str | None = None
    type: str | None = None


class NXSasPilatus(PilatusDetector):
    def __init__(
        self,
        prefix: str,
        directory_provider: DirectoryProvider,
        drv_suffix: str,
        hdf_suffix: str,
        metadata_holder: NXSasMetadataHolder,
        name: str = "",
    ):
        """Extends detector with configuration metadata required or desired
        to comply with the NXsas application definition.
        Adds all values in the NXSasMetadataHolder's configuration fields
        to the configuration of the parent device.
        Writes hdf5 files."""
        super().__init__(
            prefix,
            directory_provider,
            drv_suffix=drv_suffix,
            hdf_suffix=hdf_suffix,
            name=name,
        )
        self._metadata_holder = metadata_holder

    async def read_configuration(self) -> Dict[str, Reading]:
        return await merge_gathered_dicts(
            (
                r
                for r in (
                    super().read_configuration(),
                    self._metadata_holder.read(self.name),
                )
            )
        )

    async def describe_configuration(self) -> Dict[str, DataKey]:
        return await merge_gathered_dicts(
            (
                r
                for r in (
                    super().describe_configuration(),
                    self._metadata_holder.describe(self.name),
                )
            )
        )


class NXSasOAV(AravisDetector):
    def __init__(
        self,
        prefix: str,
        directory_provider: DirectoryProvider,
        drv_suffix: str,
        hdf_suffix: str,
        metadata_holder: NXSasMetadataHolder,
        name: str = "",
        gpio_number: AravisController.GPIO_NUMBER = 1,
    ):
        """Extends detector with configuration metadata required or desired
        to comply with the NXsas application definition.
        Adds all values in the NXSasMetadataHolder's configuration fields
        to the configuration of the parent device.
        Writes hdf5 files."""
        super().__init__(
            prefix,
            directory_provider,
            drv_suffix=drv_suffix,
            hdf_suffix=hdf_suffix,
            name=name,
            gpio_number=gpio_number,
        )
        self._metadata_holder = metadata_holder

    async def read_configuration(self) -> Dict[str, Reading]:
        return await merge_gathered_dicts(
            (
                r
                for r in (
                    super().read_configuration(),
                    self._metadata_holder.read(self.name),
                )
            )
        )

    async def describe_configuration(self) -> Dict[str, DataKey]:
        return await merge_gathered_dicts(
            (
                r
                for r in (
                    super().describe_configuration(),
                    self._metadata_holder.describe(self.name),
                )
            )
        )
