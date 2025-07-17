from collections import Counter

from pydantic import BaseModel, Field, model_validator


class ZebraMappingValidations(BaseModel):
    """Raises an exception if field set to -1 is accessed, and validate against
    multiple fields mapping to the same integer"""

    def __getattribute__(self, name: str):
        """To protect against mismatch between the Zebra configuration that a plan expects and the Zebra which has
        been instantiated, raise exception if a field which has been set to -1 is accessed."""
        value = object.__getattribute__(self, name)
        if not name.startswith("__"):
            if value == -1:
                raise UnmappedZebraException(
                    f"'{type(self).__name__}.{name}' was accessed but is set to -1. Please check the zebra mappings against the zebra's physical configuration"
                )
        return value

    @model_validator(mode="after")
    def ensure_no_duplicate_connections(self):
        """Check that TTL outputs and sources are mapped to unique integers"""

        integer_fields = {
            key: value
            for key, value in self.model_dump().items()
            if isinstance(value, int) and value != -1
        }
        counted_vals = Counter(integer_fields.values())
        integer_fields_with_duplicates = {
            k: v for k, v in integer_fields.items() if counted_vals[v] > 1
        }
        if len(integer_fields_with_duplicates):
            raise ValueError(
                f"Each field in {type(self)} must be mapped to a unique integer. Duplicate fields: {integer_fields_with_duplicates}"
            )
        return self


class ZebraTTLOutputs(ZebraMappingValidations):
    """Maps hardware to the Zebra TTL output (1-4) that they're physically wired to, or
    None if that hardware is not connected. A value of -1 means this hardware is not connected."""

    TTL_EIGER: int = Field(default=-1, ge=-1, le=4)
    TTL_PILATUS: int = Field(default=-1, ge=-1, le=4)
    TTL_FAST_SHUTTER: int = Field(default=-1, ge=-1, le=4)
    TTL_DETECTOR: int = Field(default=-1, ge=-1, le=4)
    TTL_SHUTTER: int = Field(default=-1, ge=-1, le=4)
    TTL_XSPRESS3: int = Field(default=-1, ge=-1, le=4)
    TTL_PANDA: int = Field(default=-1, ge=-1, le=4)


class ZebraSources(ZebraMappingValidations):
    """Maps internal Zebra signal source to their integer PV value"""

    DISCONNECT: int = Field(default=0, ge=0, le=63)
    IN1_TTL: int = Field(default=1, ge=0, le=63)
    IN2_TTL: int = Field(default=63, ge=0, le=63)
    IN3_TTL: int = Field(default=7, ge=0, le=63)
    IN4_TTL: int = Field(default=10, ge=0, le=63)
    PC_ARM: int = Field(default=29, ge=0, le=63)
    PC_GATE: int = Field(default=30, ge=0, le=63)
    PC_PULSE: int = Field(default=31, ge=0, le=63)
    AND3: int = Field(default=34, ge=0, le=63)
    AND4: int = Field(default=35, ge=0, le=63)
    OR1: int = Field(default=36, ge=0, le=63)
    PULSE1: int = Field(default=52, ge=0, le=63)
    PULSE2: int = Field(default=53, ge=0, le=63)
    SOFT_IN1: int = Field(default=60, ge=0, le=63)
    SOFT_IN2: int = Field(default=61, ge=0, le=63)
    SOFT_IN3: int = Field(default=62, ge=0, le=63)


class ZebraMapping(ZebraMappingValidations):
    """Mappings to locate a Zebra device's Ophyd signals based on a specific
    Zebra's hardware configuration and wiring.
    """

    # Zebra ophyd signal for connection can be accessed
    # with, eg, zebra.output.out_pvs[zebra.mapping.outputs.TTL_DETECTOR]
    outputs: ZebraTTLOutputs = ZebraTTLOutputs()

    # Zebra ophyd signal sources can be mapped to a zebra output by doing, eg,
    # bps.abs_set(zebra.output.out_pvs[zebra.mapping.outputs.TTL_DETECTOR],
    # zebra.mapping.sources.AND3)
    sources: ZebraSources = ZebraSources()

    # Which of the Zebra's four AND gates is used to control the automatic shutter, if it's being used.
    # After defining, the correct GateControl device can be accessed with, eg,
    # zebra.logic_gates.and_gates[zebra.mapping.AND_GATE_FOR_AUTO_SHUTTER]. Set to -1 if not being used.
    AND_GATE_FOR_AUTO_SHUTTER: int = Field(default=2, ge=-1, le=4)


class UnmappedZebraException(Exception):
    pass
