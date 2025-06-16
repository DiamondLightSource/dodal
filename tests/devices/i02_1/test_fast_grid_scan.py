from ophyd_async.core import init_devices

from dodal.devices.fast_grid_scan import ZebraFastGridScan
from dodal.devices.i02_1.fast_grid_scan import TwoDFastGridScan


# TODO maybe delete this as plan will test it
def test_fast_grid_scan_has_same_attributes_as_parent(RE):
    # We never call super().__init__ on the FGS device, since it needs to override
    # a lot of the attributes as soft signals
    with init_devices(mock=True):
        vmxm_fgs = TwoDFastGridScan("vmxm")
        parent_fgs = ZebraFastGridScan("parent")
    vmxm_fgs_attrs = set(vars(vmxm_fgs).keys())
    parent_fgs_attrs = set(vars(parent_fgs).keys())
    assert vmxm_fgs_attrs == parent_fgs_attrs
