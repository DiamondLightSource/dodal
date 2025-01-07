from dataclasses import dataclass


@dataclass
class ZebraMapping:
    """A set of constants which map: TTL outputs to their physically wired hardware;
    Zebra input sources to their corresponding integer PV; and some constants to help
    set up the zebra-controlled shutter.

    Raises: UnknownZebraMappingException
    To protect against mismatch between the Zebra configuration that a plan expects and the Zebra which has
    been instantiated, raise exception if a field which has been set to None is accessed.
    """

    # TTL Outputs: These constants refer to which hardware is connected to which of the
    # 4 TTL output slots on the Zebra. If None, the hardware isn't connected

    TTL_EIGER: int | None = None
    TTL_PILATUS: int | None = None
    TTL_FAST_SHUTTER: int | None = None
    TTL_DETECTOR: int | None = None
    TTL_SHUTTER: int | None = None
    TTL_XSPRESS3: int | None = None
    TTL_PANDA: int | None = None

    # Zebra signal sources. The integers refer to where the different sources are located
    # on the zebra IOC. Can be mapped to a zebra output by doing, eg,
    # bps.abs_set(zebra.output.out_pvs[TTL_DETECTOR], DISCONNECT)
    DISCONNECT: int | None = 0
    IN1_TTL: int | None = 1
    IN2_TTL: int | None = 4
    IN3_TTL: int | None = 7
    IN4_TTL: int | None = 10
    PC_ARM: int | None = 29
    PC_GATE: int | None = 30
    PC_PULSE: int | None = 31
    AND3: int | None = 34
    AND4: int | None = 35
    OR1: int | None = 36
    PULSE1: int | None = 52
    PULSE2: int | None = 53
    SOFT_IN1: int | None = 60
    SOFT_IN2: int | None = 61
    SOFT_IN3: int | None = 62

    # Remaining constants can be ignored unless the zebra controlled shutter is being used.

    # Which of the Zebra's four AND gates should be used to control the automatic shutter.
    # After defining this, the correct GateControl device can be accessed with, eg,
    # zebra.logic_gates.and_gates[AUTO_SHUTTER_GATE]
    # Leave as None if auto shutter isn't being used.
    AUTO_SHUTTER_GATE: int | None = None

    # All sources of the auto shutter AND gate. These can be configured with, eg,
    # bps.abs_set(zebra.logic_gates.and_gates[AUTO_SHUTTER_GATE].sources[AUTO_SHUTTER_INPUT_1], SOFT_IN1)
    AUTO_SHUTTER_INPUT_1: int | None = None
    AUTO_SHUTTER_INPUT_2: int | None = None
    AUTO_SHUTTER_INPUT_3: int | None = None
    AUTO_SHUTTER_INPUT_4: int | None = None

    def __getattribute__(self, name):
        """Runtime Error if an unmapped zebra constant is accessed"""

        value = object.__getattribute__(self, name)
        if value is None:
            raise UnknownZebraMappingException(
                f"'{type(self).__name__}.{name}' is None. Please check if {name} is valid for the instantiated Zebra"
            )
        return value


class UnknownZebraMappingException(Exception):
    pass


I03_ZEBRA_CONSTANTS = ZebraMapping(
    TTL_DETECTOR=1,
    TTL_SHUTTER=2,
    TTL_XSPRESS3=3,
    TTL_PANDA=4,
    AUTO_SHUTTER_GATE=2,
    AUTO_SHUTTER_INPUT_1=1,
    AUTO_SHUTTER_INPUT_2=2,
)

# TODO: Check these values
I04_ZEBRA_CONSTANTS = ZebraMapping(
    TTL_DETECTOR=1,
    TTL_SHUTTER=2,
    TTL_XSPRESS3=3,
)


I02_1_ZEBRA_CONSTANTS = ZebraMapping(
    TTL_SHUTTER=1,
    TTL_DETECTOR=2,
    TTL_XSPRESS3=3,
)

I24_ZEBRA_CONSTANTS = ZebraMapping(TTL_EIGER=1, TTL_PILATUS=2, TTL_FAST_SHUTTER=4)
