from dodal.devices.util.lookup_tables_apple2 import (
    LookupTableConfig,
)

J09DefaultLookupTableConfig = LookupTableConfig(
    mode="Mode",
    min_energy="MinEnergy",
    max_energy="MaxEnergy",
    poly_deg=[
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
    ],
    mode_name_convert={"cr": "pc", "cl": "nc"},
)
