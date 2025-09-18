from ophyd_async.core import StrictEnum


class EnergyMode(StrictEnum):
    """
    Enumeration of possible energy modes for the electron analyser.

    Attributes:
        KINETIC: Represents the kinetic energy mode.
        BINDING: Represents the binding energy mode.
    """

    KINETIC = "Kinetic"
    BINDING = "Binding"


class SelectedSource(StrictEnum):
    """
    Enumeration representing the selectable sources for the electron analyser.

    Attributes:
        SOURCE1: Represents the first source ("source1").
        SOURCE2: Represents the second source ("source2").
    """

    SOURCE1 = "source1"
    SOURCE2 = "source2"
