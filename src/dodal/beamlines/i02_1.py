"""Beamline i02-1 is also known as VMXm, or I02J"""

from dodal.common.beamlines.beamline_utils import (
    device_factory,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.attenuator.attenuator import EnumFilterAttenuator
from dodal.devices.attenuator.filter_selections import (
    I02_1FilterFourSelections,
    I02_1FilterOneSelections,
    I02_1FilterThreeSelections,
    I02_1FilterTwoSelections,
)
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i22")
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_utils_beamline(BL)


@device_factory()
def attenuator() -> EnumFilterAttenuator:
    return EnumFilterAttenuator(
        num_filters=4,
        filter_selection=[
            I02_1FilterOneSelections,
            I02_1FilterTwoSelections,
            I02_1FilterThreeSelections,
            I02_1FilterFourSelections,
        ],
        prefix="BL02J-OP-ATTN-01:",
    )
