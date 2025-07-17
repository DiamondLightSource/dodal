from ophyd_async.core import StrictEnum


class EnergyMode(StrictEnum):
    KINETIC = "Kinetic"
    BINDING = "Binding"
