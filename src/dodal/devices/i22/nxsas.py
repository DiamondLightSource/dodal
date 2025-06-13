import asyncio
from collections.abc import Awaitable, Iterable
from dataclasses import dataclass, fields
from typing import TypeVar

from bluesky.protocols import Reading
from event_model.documents.event_descriptor import DataKey
from ophyd_async.core import PathProvider
from ophyd_async.epics.adaravis import AravisDetector
from ophyd_async.epics.adpilatus import PilatusDetector

ValueAndUnits = tuple[float, str]
T = TypeVar("T")


# TODO: Remove this file as part of github.com/DiamondLightSource/dodal/issues/595
# Until which, temporarily duplicated non-public method from ophyd_async
async def _merge_gathered_dicts(
    coros: Iterable[Awaitable[dict[str, T]]],
) -> dict[str, T]:
    """Merge dictionaries produced by a sequence of coroutines.

    Can be used for merging ``read()`` or ``describe``. For instance::

        combined_read = await merge_gathered_dicts(s.read() for s in signals)
    """
    ret: dict[str, T] = {}
    for result in await asyncio.gather(*coros):
        ret.update(result)
    return ret


@dataclass
class MetadataHolder:
    # TODO: just in case this is useful more widely...
    async def describe(self, parent_name: str) -> dict[str, DataKey]:
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

    async def read(self, parent_name: str) -> dict[str, Reading]:
        def reading(value) -> Reading:
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
        path_provider: PathProvider,
        drv_suffix: str,
        fileio_suffix: str,
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
            path_provider,
            drv_suffix=drv_suffix,
            fileio_suffix=fileio_suffix,
            name=name,
        )
        self._metadata_holder = metadata_holder

    async def read_configuration(self) -> dict[str, Reading]:
        return await _merge_gathered_dicts(
            r
            for r in (
                super().read_configuration(),
                self._metadata_holder.read(self.name),
            )
        )

    async def describe_configuration(self) -> dict[str, DataKey]:
        return await _merge_gathered_dicts(
            r
            for r in (
                super().describe_configuration(),
                self._metadata_holder.describe(self.name),
            )
        )


class NXSasOAV(AravisDetector):
    def __init__(
        self,
        prefix: str,
        path_provider: PathProvider,
        drv_suffix: str,
        fileio_suffix: str,
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
            path_provider,
            drv_suffix=drv_suffix,
            fileio_suffix=fileio_suffix,
            name=name,
        )
        self._metadata_holder = metadata_holder

    async def read_configuration(self) -> dict[str, Reading]:
        return await _merge_gathered_dicts(
            r
            for r in (
                super().read_configuration(),
                self._metadata_holder.read(self.name),
            )
        )

    async def describe_configuration(self) -> dict[str, DataKey]:
        return await _merge_gathered_dicts(
            r
            for r in (
                super().describe_configuration(),
                self._metadata_holder.describe(self.name),
            )
        )
