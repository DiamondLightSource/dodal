import pytest
from ophyd_async.core import PathProvider, init_devices
from ophyd_async.epics.adpilatus import PilatusDetector

from dodal.common.beamlines.device_helpers import CAM_SUFFIX, HDF5_SUFFIX
from dodal.devices.i22.nxsas import NXSasMetadataHolder, NXSasPilatus


@pytest.fixture
def saxs(static_path_provider: PathProvider, RE) -> PilatusDetector:
    with init_devices(mock=True):
        saxs = NXSasPilatus(
            prefix="-EA-PILAT-01:",
            drv_suffix=CAM_SUFFIX,
            fileio_suffix=HDF5_SUFFIX,
            metadata_holder=NXSasMetadataHolder(
                x_pixel_size=(1.72e-1, "mm"),
                y_pixel_size=(1.72e-1, "mm"),
                distance=(
                    0.0,
                    "m",
                ),  # To get from configuration data after visit begins
            ),
            path_provider=static_path_provider,
        )
    return saxs


async def test_config_data_present(saxs: PilatusDetector):
    dc = await saxs.describe_configuration()
    for config_field in {"x_pixel_size", "y_pixel_size", "distance"}:
        config = dc[f"{saxs.name}-{config_field}"]
        assert config["units"] is not None  # type: ignore
        assert config["shape"] == []
        assert config["source"] == "calibration"
        assert config["dtype"] == "number"
    assert not hasattr(dc, f"{saxs.name}-type")
    assert dc[f"{saxs.name}-driver-acquire_time"] is not None
