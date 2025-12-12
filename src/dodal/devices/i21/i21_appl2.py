import json

from dodal.devices.insertion_device import (
    LookupTable,
)

I21_GAP_POLY_DEG_COLUMNS = [
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

I21_PHASE_POLY_DEG_COLUMNS = ["0th-order"]


# lut can be generated from the following json:
i21_json = """
{
    "lh": {"energy_entries": [{"min_energy": 0.104, "max_energy": 1.2, "poly": [0]}]},
    "lv": {"energy_entries": [{"min_energy": 0.104 "max_energy": 1.2, "poly": [24.0]}]},
    "pc": {"energy_entries": [{"min_energy": 0.104, "max_energy": 1.2, "poly": [15]}]},
    "nc": {"energy_entries": [{"min_energy": 0.104, "max_energy": 1.2, "poly": [-15]}]},
    "lh3": {"energy_entries": [{"min_energy": 0.7, "max_energy": 2.0, "poly": [0]}]}
}
"""
I21_GENERATED_PHASE_LUT = LookupTable(json.loads(i21_json))
