from ophyd_async.core import StrictEnum


class EnergyMode(StrictEnum):
    KINETIC = "Kinetic"
    BINDING = "Binding"


class SelectedSource(StrictEnum):
    SOURCE1 = "source1"
    SOURCE2 = "source2"
