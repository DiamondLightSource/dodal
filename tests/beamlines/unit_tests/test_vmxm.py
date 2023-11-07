from unittest.mock import patch

from dodal.beamlines import beamline_utils, vmxm


@patch.dict("os.environ", {"BEAMLINE": "i02-1"}, clear=True)
def test_list():
    beamline_utils.clear_devices()
    beamline_utils.set_beamline(
        "vmxm", suffix="J", beamline_prefix="BL02", insertion_prefix="SR-DI-J02"
    )
    vmxm.eiger(wait_for_connection=False)
    vmxm.fast_grid_scan(wait_for_connection=False)
    vmxm.zebra(wait_for_connection=False)

    assert beamline_utils.list_active_devices() == [
        "eiger",
        "fast_grid_scan",
        "zebra",
    ]


@patch.dict("os.environ", {"BEAMLINE": "i02-1"}, clear=True)
def test_prefixes():
    beamline_utils.clear_devices()
    beamline_utils.set_beamline(
        "vmxm", suffix="J", beamline_prefix="BL02J", insertion_prefix="SR-DI-J02"
    )
    eiger = vmxm.eiger(wait_for_connection=False)
    fgs = vmxm.fast_grid_scan(wait_for_connection=False)
    zebra = vmxm.zebra(wait_for_connection=False)

    assert eiger.prefix == "BL02J-EA-EIGER-01:"
    assert fgs.prefix == "BL02J-MO-SAMP-11:FGS:"
    assert zebra.prefix == "BL02J-EA-ZEBRA-01:"
