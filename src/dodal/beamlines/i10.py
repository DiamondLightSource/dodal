from dodal.device_manager import DeviceManager
from dodal.devices.i10.i10_devices_configs import (
    devices_det_slits,
    devices_diagnostics_i,
    devices_diffractometer,
    devices_femto,
    devices_femto_det,
    devices_idd,
    devices_idu,
    devices_mirror_i,
    devices_pa_stage,
    devices_pin_hole,
    devices_rasor_temperature_controller,
    devices_sample_stage,
    devices_scaler_cards,
    devices_shared_diagnostics,
    devices_shared_mirror,
    devices_shared_slit,
    devices_slit_i,
    devices_sr570,
    devices_sr570_det,
    pgm_device,
)

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


"""------------------i10 i devices-----------------------------------------"""
"""Mirrors"""
devices.include(devices_mirror_i)

"""Optic slits"""

devices.include(devices_slit_i)


"""Diagnostics"""
devices.include(devices_diagnostics_i)


"""Rasor devices"""
"""Stage devices"""
devices.include(devices_pin_hole)
devices.include(devices_det_slits)
devices.include(devices_diffractometer)
devices.include(devices_pa_stage)
devices.include(devices_sample_stage)
"""Temperature controller"""
devices.include(devices_rasor_temperature_controller)
""" detectors """
"""Current amplifiers"""
devices.include(devices_femto)
devices.include(devices_sr570)
"""Scaler cards"""
devices.include(devices_scaler_cards)
"""Detectors"""
devices.include(
    devices_femto_det
)  # Must include devices_scaler_cards and devices_femto
devices.include(
    devices_sr570_det
)  # Must include devices_scaler_cards and devices_sr570

"""---------------------------------------------------------------------"""
