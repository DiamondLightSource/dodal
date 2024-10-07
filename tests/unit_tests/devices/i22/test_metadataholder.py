import pytest
from ophyd_async.core import DeviceCollector, PathProvider
from ophyd_async.epics.adpilatus import PilatusDetector

from dodal.devices.i22.nxsas import NXSasMetadataHolder, NXSasPilatus


@pytest.fixture
def saxs(static_path_provider: PathProvider, RE) -> PilatusDetector:
    with DeviceCollector(mock=True):
        saxs = NXSasPilatus(
            prefix="-EA-PILAT-01:",
            drv_suffix="CAM:",
            hdf_suffix="HDF5:",
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
    assert dc[f"{saxs.name}-drv-acquire_time"] is not None
