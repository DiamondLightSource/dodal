from dodal.beamlines import beamline_utils, i02_1


def test_list():
    beamline_utils.clear_devices()
    i02_1.eiger(wait_for_connection=False)
    i02_1.fast_grid_scan(wait_for_connection=False)
    i02_1.zebra(wait_for_connection=False)

    assert beamline_utils.list_active_devices() == [
        "eiger",
        "fast_grid_scan",
        "zebra",
    ]
