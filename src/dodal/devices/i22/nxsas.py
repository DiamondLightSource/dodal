from typing import Dict, Tuple

from event_model.documents.event_descriptor import DataKey
from ophyd_async.core import (
    ConfigSignal,
    DirectoryProvider,
    StandardReadable,
    soft_signal_r_and_setter,
)
from ophyd_async.epics.areadetector import AravisDetector, PilatusDetector
from ophyd_async.epics.areadetector.aravis import AravisController


class NXSasMetadataHolder(StandardReadable):
    ValueAndUnits = Tuple[float, str]
    """
    Required fields for NXDetectors that are used in an NXsas application definition
    """

    def __init__(
        self,
        distance: ValueAndUnits,
        x_pixel_size: ValueAndUnits,
        y_pixel_size: ValueAndUnits,
        beam_center_x: ValueAndUnits | None = None,
        beam_center_y: ValueAndUnits | None = None,
        aequetorial_angle: ValueAndUnits | None = None,
        azimuthal_angle: ValueAndUnits | None = None,
        polar_angle: ValueAndUnits | None = None,
        rotation_angle: ValueAndUnits | None = None,
        threshold_energy: ValueAndUnits | None = None,
        serial_number: str | None = None,
        sensor_material: str | None = None,
        sensor_thickness: ValueAndUnits | None = None,
        description: str | None = None,
        type: str | None = None,
        prefix: str = "",
        name: str = "",
    ):
        with self.add_children_as_readables(ConfigSignal):
            self.distance, _ = soft_signal_r_and_setter(
                float, distance[0], units=distance[1]
            )
            self.x_pixel_size, _ = soft_signal_r_and_setter(
                float, x_pixel_size[0], units=x_pixel_size[1]
            )
            self.y_pixel_size, _ = soft_signal_r_and_setter(
                float, y_pixel_size[0], units=y_pixel_size[1]
            )
            if polar_angle is not None:
                self.polar_angle, _ = soft_signal_r_and_setter(
                    float, polar_angle[0], units=polar_angle[1]
                )
            else:
                self.polar_angle = None
            if azimuthal_angle is not None:
                self.azimuthal_angle, _ = soft_signal_r_and_setter(
                    float, azimuthal_angle[0], units=azimuthal_angle[1]
                )
            else:
                self.azimuthal_angle = None
            if rotation_angle is not None:
                self.rotation_angle, _ = soft_signal_r_and_setter(
                    float, rotation_angle[0], units=rotation_angle[1]
                )
            else:
                self.rotation_angle = None
            if aequetorial_angle is not None:
                self.aequetorial_angle, _ = soft_signal_r_and_setter(
                    float, aequetorial_angle[0], aequetorial_angle[1]
                )
            else:
                self.aequetorial_angle = None
            if beam_center_x is not None:
                self.beam_center_x, _ = soft_signal_r_and_setter(
                    float, beam_center_x[0], units=beam_center_x[1]
                )
            else:
                self.beam_center_x = None
            if beam_center_y is not None:
                self.beam_center_y, _ = soft_signal_r_and_setter(
                    float, beam_center_y[0], units=beam_center_y[1]
                )
            else:
                self.beam_center_y = None
            if sensor_material is not None:
                self.sensor_material, _ = soft_signal_r_and_setter(str, sensor_material)
            else:
                self.sensor_material = None
            if description is not None:
                self.description, _ = soft_signal_r_and_setter(str, description)
            else:
                self.description = None
            if type is not None:
                self.type, _ = soft_signal_r_and_setter(str, type)
            else:
                self.type = None
            if serial_number is not None:
                self.serial_number, _ = soft_signal_r_and_setter(str, serial_number)
            else:
                self.serial_number = None
            if sensor_thickness is not None:
                self.sensor_thickness, _ = soft_signal_r_and_setter(
                    float, sensor_thickness[0], units=sensor_thickness[1]
                )
            else:
                self.sensor_thickness = None
            if threshold_energy is not None:
                self.threshold_energy, _ = soft_signal_r_and_setter(
                    float, threshold_energy[0], threshold_energy[1]
                )
            else:
                self.threshold_energy = None


class NXSasPilatus(PilatusDetector):
    def __init__(
        self,
        prefix: str,
        directory_provider: DirectoryProvider,
        drv_suffix,
        hdf_suffix,
        metadata_holder: NXSasMetadataHolder,
        name: str = "",
    ):
        super().__init__(
            prefix,
            directory_provider,
            drv_suffix=drv_suffix,
            hdf_suffix=hdf_suffix,
            name=name,
        )
        self._metadata_holder = metadata_holder

    async def describe_configuration(self) -> Dict[str, DataKey]:
        return {
            **await super().describe_configuration(),
            **await self._metadata_holder.describe_configuration(),
        }


class NXSasOAV(AravisDetector):
    def __init__(
        self,
        prefix: str,
        directory_provider: DirectoryProvider,
        drv_suffix,
        hdf_suffix,
        metadata_holder: NXSasMetadataHolder,
        name: str = "",
        gpio_number: AravisController.GPIO_NUMBER = 1,
    ):
        super().__init__(
            prefix,
            directory_provider,
            drv_suffix=drv_suffix,
            hdf_suffix=hdf_suffix,
            name=name,
            gpio_number=gpio_number,
        )
        self._metadata_holder = metadata_holder

    async def describe_configuration(self) -> Dict[str, DataKey]:
        return {
            **await super().describe_configuration(),
            **await self._metadata_holder.describe_configuration(),
        }
