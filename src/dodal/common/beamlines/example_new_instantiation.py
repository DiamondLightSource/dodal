from ophyd_async.core import Device as OphydV2Device

from dodal.common.beamlines.device_factory import device_factory


class XYZDetector(OphydV2Device):
    def __init__(self, prefix: str, *args, **kwargs):
        self.prefix = prefix
        super().__init__(*args, **kwargs)

    @property
    def hints(self):
        raise NotImplementedError


beamline_prefix = "example:"


@device_factory(default_use_mock_at_connection=True, default_timeout_for_connect=10)
def new_detector_xyz():
    """Create an XYZ detector with specific settings."""
    return XYZDetector(name="det1", prefix=f"{beamline_prefix}xyz:")


@device_factory(
    eager=True, default_use_mock_at_connection=True, default_timeout_for_connect=10
)
def detector_xyz_variant():
    """Create an XYZ detector with specific settings."""
    return XYZDetector(name="det2-variant", prefix=f"{beamline_prefix}xyz:")
