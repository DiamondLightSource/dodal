from unittest.mock import ANY

from ophyd_async.testing import assert_configuration, partial_reading

from dodal.devices.beamlines.i05_shared import LensMode, PassEnergy
from dodal.devices.electron_analyser.mbs import MbsDetector, MbsRegion


async def test_mbs_detector_read_configuration(i05_mbs_analyser: MbsDetector) -> None:
    prefix = i05_mbs_analyser.driver.name + "-"
    region = MbsRegion[LensMode, PassEnergy](
        lens_mode=LensMode.L4_ANG0_D8, pass_energy=PassEnergy.PE001
    )
    await i05_mbs_analyser.set(region)
    await assert_configuration(
        i05_mbs_analyser,
        {
            f"{prefix}region_name": partial_reading(region.name),
            f"{prefix}energy_mode": partial_reading(region.energy_mode),
            f"{prefix}acquisition_mode": partial_reading(region.acquisition_mode),
            f"{prefix}lens_mode": partial_reading(region.lens_mode),
            f"{prefix}low_energy": partial_reading(region.low_energy),
            f"{prefix}centre_energy": partial_reading(region.centre_energy),
            f"{prefix}high_energy": partial_reading(region.high_energy),
            f"{prefix}deflector_x": partial_reading(region.deflector_x),
            f"{prefix}energy_step": partial_reading(ANY),
            f"{prefix}pass_energy": partial_reading(region.pass_energy),
            f"{prefix}slices": partial_reading(ANY),
            f"{prefix}iterations": partial_reading(region.iterations),
            f"{prefix}total_steps": partial_reading(ANY),
            f"{prefix}acquire_time": partial_reading(region.acquire_time),
            f"{prefix}acquire_period": partial_reading(ANY),
            f"{prefix}total_time": partial_reading(ANY),
            f"{prefix}energy_axis": partial_reading(ANY),
            f"{prefix}angle_axis": partial_reading(ANY),
            f"{prefix}psu_mode": partial_reading(ANY),
            f"{prefix}dither_steps": partial_reading(ANY),
            f"{prefix}spin_offset": partial_reading(ANY),
            f"{prefix}array_size_x": partial_reading(ANY),
            f"{prefix}array_size_y": partial_reading(ANY),
            f"{prefix}min_x": partial_reading(ANY),
            f"{prefix}min_y": partial_reading(ANY),
            f"{prefix}max_x": partial_reading(ANY),
            f"{prefix}max_y": partial_reading(ANY),
            f"{i05_mbs_analyser.name}-binding_energy_axis": partial_reading(ANY),
        },
    )
