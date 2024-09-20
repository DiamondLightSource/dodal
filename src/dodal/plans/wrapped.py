from collections.abc import Mapping
from typing import Annotated, Any

import bluesky.plans as bp
from bluesky.protocols import Readable
from pydantic import Field, PositiveFloat, validate_call

from dodal.common import MsgGenerator
from dodal.plan_stubs import attach_data_session_metadata_decorator


@attach_data_session_metadata_decorator()
@validate_call(config={"arbitrary_types_allowed": True})
def count(
    detectors: Annotated[
        set[Readable],
        Field(
            description="Set of readable devices, will take a reading at each point",
            min_length=1,
        ),
    ],
    num: Annotated[int, Field(description="Number of frames to collect", ge=1)] = 1,
    delay: Annotated[
        PositiveFloat | list[PositiveFloat] | None,
        Field(
            description="Delay between readings: if list, len(delay) == num - 1 and \
            the delays are between each point, if value or None is the delay for every \
            gap",
            json_schema_extra={"units": "s"},
        ),
    ] = None,
    metadata: Mapping[str, Any] | None = None,
) -> MsgGenerator:
    if isinstance(delay, list):
        assert (
            delays := len(delay)
        ) == num - 1, f"Number of delays given must be {num - 1}: was given {delays} "
    yield from bp.count(detectors, num, delay=delay, md=metadata or {})
