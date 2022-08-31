import pytest
import typing
from ophyd import Device
from dodal import i03, s03

def get_devices(module_dict) -> typing.Dict[str, Device]:
    """This goes through the functions in the beamline module and calls any that provide a 
    Device to connect to and are not flagged as skip connection.
    """
    devices = {}
    for name, maybe_func in module_dict.items():
        try:
            return_type = typing.get_type_hints(maybe_func)["return"]
        except (TypeError, KeyError):
            # This isn't a function or has no return type
            continue
        if not issubclass(return_type, Device):
            continue
        if hasattr(maybe_func, "skip_connection"):
            continue
        devices[name] = maybe_func()
    return devices

@pytest.mark.dls_network
@pytest.mark.parametrize("beamline", [i03, s03])
def test_pvs_connect(beamline):
    """This is a system test that checks the PVs are correct for the currently running beamlines.
    It will fail outside the DLS network and failure may indicate either an issue with dodal 
    or the beamlines themselves."""
    devices = get_devices(beamline.__dict__)
    for name, device in devices.items():
        device.wait_for_connection()