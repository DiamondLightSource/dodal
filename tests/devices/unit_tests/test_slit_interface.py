from dodal.devices.slits.S5_BL02J_AL_SLITS_95 import S5_BL02J_AL_SLITS_95 as Slit

import random


def parsed_read(component):
    res = component.read()
    return res


import pdb


def test_set():
    pdb.set_trace()
    slit = Slit(name="slit", prefix="BL02J-AL-SLITS-95:")
    slit.wait_for_connection()

    target_values = [round(random.random() * 3, 3) for i in range(4)]

    status = slit.set(*target_values)
    status.wait()

    res = parsed_read(slit.x_size)
    breakpoint()

    # assert False
