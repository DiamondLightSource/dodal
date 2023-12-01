from enum import Enum

from ophyd import Component, Device, EpicsMotor, EpicsSignal, Signal


class MirrorStripe(Enum):
    RHODIUM = "Rhodium"
    BARE = "Bare"
    PLATINUM = "Platinum"


class MirrorVoltageSignal(Signal):
    def set(self, value, *, timeout=None, settle_time=None, **kwargs):
        actual_v, setpoint_v, demand_accepted_v = self.parent.components_for_channel(
            self.name
        )
        print(actual_v)


class VoltageDevice(Device):
    voltage_signal: MirrorVoltageSignal = Component(MirrorVoltageSignal)


class VFMMirrorVoltages(Device):
    _channel14_actual_v: EpicsSignal = Component(EpicsSignal, "BM:V14R")
    _channel14_setpoint_v: EpicsSignal = Component(EpicsSignal, "BM:V14D")
    _channel14_demand_accepted: EpicsSignal = Component(EpicsSignal, "BM:V14DSEV")
    _channel15_actual_v: EpicsSignal = Component(EpicsSignal, "BM:V15R")
    _channel15_setpoint_v: EpicsSignal = Component(EpicsSignal, "BM:V15D")
    _channel15_demand_accepted: EpicsSignal = Component(EpicsSignal, "BM:V15DSEV")
    _channel16_actual_v: EpicsSignal = Component(EpicsSignal, "BM:V16R")
    _channel16_setpoint_v: EpicsSignal = Component(EpicsSignal, "BM:V16D")
    _channel16_demand_accepted: EpicsSignal = Component(EpicsSignal, "BM:V16DSEV")
    _channel17_actual_v: EpicsSignal = Component(EpicsSignal, "BM:V17R")
    _channel17_setpoint_v: EpicsSignal = Component(EpicsSignal, "BM:V17D")
    _channel17_demand_accepted: EpicsSignal = Component(EpicsSignal, "BM:V17DSEV")
    _channel18_actual_v: EpicsSignal = Component(EpicsSignal, "BM:V18R")
    _channel18_setpoint_v: EpicsSignal = Component(EpicsSignal, "BM:V18D")
    _channel18_demand_accepted: EpicsSignal = Component(EpicsSignal, "BM:V18DSEV")
    _channel19_actual_v: EpicsSignal = Component(EpicsSignal, "BM:V19R")
    _channel19_setpoint_v: EpicsSignal = Component(EpicsSignal, "BM:V19D")
    _channel19_demand_accepted: EpicsSignal = Component(EpicsSignal, "BM:V19DSEV")
    _channel20_actual_v: EpicsSignal = Component(EpicsSignal, "BM:V20R")
    _channel20_setpoint_v: EpicsSignal = Component(EpicsSignal, "BM:V20D")
    _channel20_demand_accepted: EpicsSignal = Component(EpicsSignal, "BM:V20DSEV")
    _channel21_actual_v: EpicsSignal = Component(EpicsSignal, "BM:V21R")
    _channel21_setpoint_v: EpicsSignal = Component(EpicsSignal, "BM:V21D")
    _channel21_demand_accepted: EpicsSignal = Component(EpicsSignal, "BM:V21DSEV")

    channel14_voltage = Component(MirrorVoltageSignal, "V14")
    channel15_voltage = Component(MirrorVoltageSignal, "V15")
    channel16_voltage = Component(MirrorVoltageSignal, "V16")
    channel17_voltage = Component(MirrorVoltageSignal, "V17")
    channel18_voltage = Component(MirrorVoltageSignal, "V18")
    channel19_voltage = Component(MirrorVoltageSignal, "V19")
    channel20_voltage = Component(MirrorVoltageSignal, "V20")
    channel21_voltage = Component(MirrorVoltageSignal, "V21")

    voltage_channels: list[MirrorVoltageSignal] = [
        channel14_voltage,
        channel15_voltage,
        channel16_voltage,
        channel17_voltage,
        channel18_voltage,
        channel19_voltage,
        channel20_voltage,
        channel21_voltage,
    ]

    _components_for_channel = {
        "V14": (_channel14_actual_v, _channel14_setpoint_v, _channel14_demand_accepted),
        "V15": (_channel15_actual_v, _channel15_setpoint_v, _channel15_demand_accepted),
        "V16": (_channel16_actual_v, _channel16_setpoint_v, _channel16_demand_accepted),
        "V17": (_channel17_actual_v, _channel17_setpoint_v, _channel17_demand_accepted),
        "V18": (_channel18_actual_v, _channel18_setpoint_v, _channel18_demand_accepted),
        "V19": (_channel19_actual_v, _channel19_setpoint_v, _channel19_demand_accepted),
        "V20": (_channel20_actual_v, _channel20_setpoint_v, _channel20_demand_accepted),
        "V21": (_channel21_actual_v, _channel21_setpoint_v, _channel21_demand_accepted),
    }

    def components_for_channel(self, name) -> tuple[Signal, Signal, Signal]:
        return self._components_for_channel[name]


class FocusingMirror(Device):
    """Focusing Mirror"""

    yaw_mrad: EpicsMotor = Component(EpicsMotor, "YAW")
    pitch_mrad: EpicsMotor = Component(EpicsMotor, "PITCH")
    fine_pitch_mm: EpicsMotor = Component(EpicsMotor, "FPMTR")
    roll_mrad: EpicsMotor = Component(EpicsMotor, "ROLL")
    vert_mm: EpicsMotor = Component(EpicsMotor, "VERT")
    lat_mm: EpicsMotor = Component(EpicsMotor, "LAT")
    jack1_mm: EpicsMotor = Component(EpicsMotor, "Y1")
    jack2_mm: EpicsMotor = Component(EpicsMotor, "Y2")
    jack3_mm: EpicsMotor = Component(EpicsMotor, "Y3")
    translation1_mm: EpicsMotor = Component(EpicsMotor, "X1")
    translation2_mm: EpicsMotor = Component(EpicsMotor, "X2")

    stripe: EpicsSignal = Component(EpicsSignal, "STRP:DVAL", string=True)
    # apply the current set stripe setting
    apply_stripe: EpicsSignal = Component(EpicsSignal, "CHANGE.PROC")
    voltage_lookup_table_path: str = (
        "/dls_sw/i03/software/daq_configuration/json/mirrorFocus.json"
    )

    # This needs to be configured in beamline setup as differs between mirrors
    voltage_channels: list[MirrorVoltageSignal] = []
