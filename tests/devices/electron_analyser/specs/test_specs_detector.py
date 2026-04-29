from unittest.mock import ANY

from ophyd_async.testing import assert_configuration, partial_reading

from dodal.devices.beamlines.b07 import LensMode
from dodal.devices.beamlines.b07_shared import PsuMode
from dodal.devices.electron_analyser.specs import SpecsDetector, SpecsRegion


async def test_specs_detector_read_configuration(b07b_specs150: SpecsDetector) -> None:
    prefix = b07b_specs150.driver.name + "-"
    region = SpecsRegion[LensMode, PsuMode](
        lens_mode=LensMode.HIGH_ANGULAR_DISPERSION, psu_mode=PsuMode.V10
    )
    await b07b_specs150.set(region)
    await assert_configuration(
        b07b_specs150,
        {
            b07b_specs150.binding_energy_axis.name: partial_reading(ANY),
            f"{prefix}region_name": partial_reading(region.name),
            f"{prefix}energy_mode": partial_reading(region.energy_mode),
            f"{prefix}acquisition_mode": partial_reading(region.acquisition_mode),
            f"{prefix}snapshot_values": partial_reading(region.values),
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
            f"{prefix}psu_mode": partial_reading(ANY),
        },
    )
