from dodal.beamlines.i10_devices import (
    devices_diagnostics_j,
    devices_em_temperature_controller,
    devices_idd,
    devices_idu,
    devices_mirror_j,
    devices_shared_diagnostics,
    devices_shared_mirror,
    devices_shared_slit,
    devices_slit_j,
    pgm_device,
)
from dodal.device_manager import DeviceManager

devices = DeviceManager()

"""------------------shared-----------------------------------------"""
"""Insertion Devices"""

devices.include(devices_idd)
devices.include(devices_idu)

"""Mirrors"""
devices.include(devices_shared_mirror)

"""Slits"""
devices.include(devices_shared_slit)

"""Diagnostics"""
devices.include(devices_shared_diagnostics)

"""Energy"""
devices.include(pgm_device)


"""------------------i10 j devices-----------------------------------------"""

"""Mirrors"""
devices.include(devices_mirror_j)
"""Diagnostics"""
devices.include(devices_diagnostics_j)

"""Optic slits """
devices.include(devices_slit_j)

"""EM devices"""
devices.include(devices_em_temperature_controller)
