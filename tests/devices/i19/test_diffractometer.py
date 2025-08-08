from dodal.devices.i19.diffractometer import DetectorMotion, FourCircleDiffractometer


def test_diffractometer_created_without_errors():
    diff = FourCircleDiffractometer("", "test_diffractometer")
    assert isinstance(diff, FourCircleDiffractometer)
    assert isinstance(diff.det_stage, DetectorMotion)
