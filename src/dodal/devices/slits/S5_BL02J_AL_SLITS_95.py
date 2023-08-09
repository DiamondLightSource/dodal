from ophyd import Device, Component
from bluesky.protocols import Movable

from .slit_motor import SlitMotor
from .gap_and_centre_slit_base_classes import GapAndCentreSlit2d


class S5_BL02J_AL_SLITS_95(GapAndCentreSlit2d):
    """Class to interact with slit simulator set up as BL02J temporary equipment.
    
    Many thanks to Andrew Foster!
    """
    y_plus: Device = Component(SlitMotor, "Y:PLUS")
    y_minus: Device = Component(SlitMotor, "Y:MINUS")
    
    x_plus: Device = Component(SlitMotor, "X:PLUS")
    x_minus: Device = Component(SlitMotor, "X_MINUS")

    y_size: Device = Component(SlitMotor, "Y:SIZE")
    y_centre: Device = Component(SlitMotor, "Y:CENTRE")

    x_size: Device = Component(SlitMotor, "X:SIZE")
    x_centre: Device = Component(SlitMotor, "X:CENTRE")
