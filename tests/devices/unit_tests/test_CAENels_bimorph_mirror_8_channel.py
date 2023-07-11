import pytest
from bluesky import RunEngine

from dodal.devices.bimorph_mirrors.CAENels_bimorph_mirror_8_channel import (
    CAENelsBimorphMirror8Channel,
)


def test_reads():
    bimorph = CAENelsBimorphMirror8Channel(name="bimorph", prefix="BL02J-EA-IOC-97:G0:")
    bimorph.read()
