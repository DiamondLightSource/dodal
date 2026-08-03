from typing import Final

from dodal.common.general_maths.interval import OpenInterval
from dodal.devices.beamlines.i19.transmission.specification_types import (
    ThinWedgeTaperSpecification,
    WedgeAbsorberSpecification,
    WedgeMotorScaleSpecification,
)

# X motor for secondary wedge

RESIN_WEDGE_TAPER: Final = ThinWedgeTaperSpecification(taper_cotangent=7.63359)
RESIN_WEDGE_BUBBLE_AVOIDANCE_1: Final = OpenInterval(lower=17.66, upper=18.82)
RESIN_EXCLUSIONS: Final[tuple[OpenInterval, ...]] = (RESIN_WEDGE_BUBBLE_AVOIDANCE_1,)

X_MOTOR_SCALE: Final = WedgeMotorScaleSpecification(
    axis_label="x",
    tip=-3.959,
    out=0.1,
    threshold=1.5,
    maximum=75.0,
)

# Y motor for primary wedge

ALUMINIUM_WEDGE_TAPER: Final = ThinWedgeTaperSpecification(taper_cotangent=9.3985)

# Y motor for aluminium (primary) wedge
Y_MOTOR_SCALE: Final = WedgeMotorScaleSpecification(
    axis_label="y", tip=5.06, out=5.0, threshold=8.9, maximum=98.0
)

PRIMARY_WEDGE_SPECIFICATION: Final = WedgeAbsorberSpecification(shape=ALUMINIUM_WEDGE_TAPER,
                                                                motor_coordinates=X_MOTOR_SCALE)
