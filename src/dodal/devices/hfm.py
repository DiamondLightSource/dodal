from ophyd import Component, Device, EpicsMotor


class HFM(Device):
    """Horizontal Focusing Mirror"""

    yaw_mrad: EpicsMotor = Component(EpicsMotor, "-OP-HFM-01:YAW")
    pitch_mrad: EpicsMotor = Component(EpicsMotor, "-OP-HFM-01:PITCH")
    fine_pitch_mm: EpicsMotor = Component(EpicsMotor, "-OP-HFM-01:FPMTR")
    roll_mrad: EpicsMotor = Component(EpicsMotor, "-OP-HFM-01:ROLL")
    vert_mm: EpicsMotor = Component(EpicsMotor, "-OP-HFM-01:VERT")
    lat_mm: EpicsMotor = Component(EpicsMotor, "-OP-HFM-01:LAT")
    jack1_mm: EpicsMotor = Component(EpicsMotor, "-OP-HFM-01:Y1")
    jack2_mm: EpicsMotor = Component(EpicsMotor, "-OP-HFM-01:Y2")
    jack3_mm: EpicsMotor = Component(EpicsMotor, "-OP-HFM-01:Y3")
    translation1_mm: EpicsMotor = Component(EpicsMotor, "-OP-HFM-01:X1")
    translation2_mm: EpicsMotor = Component(EpicsMotor, "-OP-HFM-01:X2")
