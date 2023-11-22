from ophyd import Component, Device, EpicsMotor


class VFM(Device):
    """Vertical Focusing Mirror"""

    yaw_mrad: EpicsMotor = Component(EpicsMotor, "-OP-VFM-01:YAW")
    pitch_mrad: EpicsMotor = Component(EpicsMotor, "-OP-VFM-01:PITCH")
    fine_pitch_mm: EpicsMotor = Component(EpicsMotor, "-OP-VFM-01:FPMTR")
    roll_mrad: EpicsMotor = Component(EpicsMotor, "-OP-VFM-01:ROLL")
    vert_mm: EpicsMotor = Component(EpicsMotor, "-OP-VFM-01:VERT")
    lat_mm: EpicsMotor = Component(EpicsMotor, "-OP-VFM-01:LAT")
    jack1_mm: EpicsMotor = Component(EpicsMotor, "-OP-VFM-01:Y1")
    jack2_mm: EpicsMotor = Component(EpicsMotor, "-OP-VFM-01:Y2")
    jack3_mm: EpicsMotor = Component(EpicsMotor, "-OP-VFM-01:Y3")
    translation1_mm: EpicsMotor = Component(EpicsMotor, "-OP-VFM-01:X1")
    translation2_mm: EpicsMotor = Component(EpicsMotor, "-OP-VFM-01:X2")
