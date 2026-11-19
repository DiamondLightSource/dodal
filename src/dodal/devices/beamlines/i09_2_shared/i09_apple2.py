from dodal.devices.insertion_device import Pol, StaticPolynomialEnergyMotorLookup
from dodal.devices.insertion_device.lookup_table_models import ROW_PHASE_CIRCULAR

J09_GAP_POLY_DEG_COLUMNS = [
    "9th-order",
    "8th-order",
    "7th-order",
    "6th-order",
    "5th-order",
    "4th-order",
    "3rd-order",
    "2nd-order",
    "1st-order",
    "0th-order",
]

JO9_MAX_PHASE = ROW_PHASE_CIRCULAR * 2
J09_ROW_PHASE_CIRCULAR = ROW_PHASE_CIRCULAR

J09_PHASE_ENERGY_MOTOR_LOOKUP = StaticPolynomialEnergyMotorLookup(
    min_value=0.1,
    max_value=2.1,
    poly_params={
        Pol.LH: [0],
        Pol.LV: [JO9_MAX_PHASE],
        Pol.PC: [J09_ROW_PHASE_CIRCULAR],
        Pol.NC: [-J09_ROW_PHASE_CIRCULAR],
        Pol.LH3: [0],
    },
)
