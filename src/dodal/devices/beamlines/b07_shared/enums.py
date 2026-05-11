from ophyd_async.core import SupersetEnum


class PsuMode(SupersetEnum):
    V3500 = "3.5kV"
    V1500 = "1.5kV"
    V400 = "400V"
    V100 = "100V"
    V10 = "10V"
    # This is connected to the device separately and will only have "Not connected" as
    # option if disconnected. Once it is connected, "Not connected" is replaced with the
    # options above. This is also why this must be a SupersetEnum.
    NOT_CONNECTED = "Not connected"
