from ophyd_async.core import SignalR, StandardReadable


class BeamsizeBase(StandardReadable):
    x_um: SignalR[float]
    y_um: SignalR[float]

    def __init__(self, name="beamsize"):
        super().__init__(name=name)
