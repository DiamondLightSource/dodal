from dodal.devices.slits.s5_blo2j_al_slits_95 import S5Bl02jAlSlits as Slit

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

    results = [round(result, 3) for result in results]

    assert all(
        [
            abs(target - result) <= 0.001
            for target, result in zip(target_values, results)
        ]
    ), f"target: {target_values}, results: {results}"

    # probably good enough...
