from dodal.devices.slits.S5_BL02J_AL_SLITS_95 import S5_BL02J_AL_SLITS_95 as Slit

import random
import pytest


def parsed_read(component):
    description = component.describe()
    res = component.read()
    return res[description[component.name]["source"]]["value"]


@pytest.mark.slits
def test_set():
    slit = Slit(name="slit", prefix="BL02J-AL-SLITS-95:")
    slit.wait_for_connection()

    target_values = [round(random.random(), 3) for i in range(4)]

    status = slit.set(target_values)
    status.wait()

    results = [
        parsed_read(slit.x_centre),
        parsed_read(slit.x_size),
        parsed_read(slit.y_centre),
        parsed_read(slit.y_size),
    ]

    assert all(
        [target == round(value, 3) for target, value in zip(target_values, results)]
    )

    # probably good enough...
