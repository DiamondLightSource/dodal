from unittest.mock import ANY

from ophyd_async.testing import assert_configuration, partial_reading

from dodal.devices.beamlines.i09 import LensMode, PassEnergy
from dodal.devices.electron_analyser.vgscienta import VGScientaDetector, VGScientaRegion


async def test_vgscienta_detector_read_configuration(ew4000: VGScientaDetector) -> None:
    prefix = ew4000.driver.name + "-"
    region = VGScientaRegion[LensMode, PassEnergy](
        lens_mode=LensMode.ANGULAR45, pass_energy=PassEnergy.E10
    )
    await ew4000.set(region)
    await assert_configuration(
        ew4000,
        {
            ew4000.binding_energy_axis.name: partial_reading(ANY),
            f"{prefix}region_name": partial_reading(region.name),
            f"{prefix}energy_mode": partial_reading(region.energy_mode),
            f"{prefix}acquisition_mode": partial_reading(region.acquisition_mode),
            f"{prefix}lens_mode": partial_reading(region.lens_mode),
            f"{prefix}low_energy": partial_reading(region.low_energy),
            f"{prefix}centre_energy": partial_reading(region.centre_energy),
            f"{prefix}high_energy": partial_reading(region.high_energy),
            f"{prefix}energy_step": partial_reading(region.energy_step),
            f"{prefix}pass_energy": partial_reading(region.pass_energy),
            f"{prefix}slices": partial_reading(region.slices),
            f"{prefix}iterations": partial_reading(region.iterations),
            f"{prefix}total_steps": partial_reading(ANY),
            f"{prefix}acquire_time": partial_reading(region.acquire_time),
            f"{prefix}total_time": partial_reading(ANY),
            f"{prefix}energy_axis": partial_reading(ANY),
            f"{prefix}angle_axis": partial_reading(ANY),
            f"{prefix}detector_mode": partial_reading(region.detector_mode),
            f"{prefix}region_min_x": partial_reading(region.min_x),
            f"{prefix}region_size_x": partial_reading(region.size_x),
            f"{prefix}sensor_max_size_x": partial_reading(ANY),
            f"{prefix}region_min_y": partial_reading(region.min_y),
            f"{prefix}region_size_y": partial_reading(region.size_y),
            f"{prefix}sensor_max_size_y": partial_reading(ANY),
            f"{prefix}psu_mode": partial_reading(ANY),
        },
    )
