from bluesky.protocols import Movable
from ophyd_async.core import StandardReadable


class BimorphMirror(StandardReadable, Movable):
    def __init__(self, prefix: str, name="", number_of_channels: int):
        ...
