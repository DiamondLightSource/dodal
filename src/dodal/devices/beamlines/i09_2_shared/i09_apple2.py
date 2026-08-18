from dodal.devices.insertion_device import EnergyCoverage, LookupTable, Pol

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

J09_PHASE_POLY_DEG_COLUMNS = ["0th-order"]

PHASE_LOOKUP_TABLE = LookupTable(
    root={
        Pol.LH: EnergyCoverage.generate(
            min_energies=[0.104],
            max_energies=[1.2],
            poly1d_params=[[0]],
        ),
        Pol.LV: EnergyCoverage.generate(
            min_energies=[0.22],
            max_energies=[1.0],
            poly1d_params=[[24.0]],
        ),
        Pol.PC: EnergyCoverage.generate(
            min_energies=[0.145],
            max_energies=[1.2],
            poly1d_params=[[15.0]],
        ),
        Pol.NC: EnergyCoverage.generate(
            min_energies=[0.145],
            max_energies=[1.2],
            poly1d_params=[[-15.0]],
        ),
        Pol.LH3: EnergyCoverage.generate(
            min_energies=[0.7],
            max_energies=[2.0],
            poly1d_params=[[0]],
        ),
    }
)
