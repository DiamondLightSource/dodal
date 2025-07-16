from ophyd_async.core import DeviceVector, SignalDatatypeT
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw


def create_rw_device_vector(
    prefix: str,
    no_channels: int,
    write_pv: str,
    read_pv: str,
    signal_type: type[SignalDatatypeT],
    zero_pv_index: bool = False,
) -> DeviceVector:
    if zero_pv_index:
        offset = -1
    else:
        offset = 0

    return DeviceVector(
        {
            i: epics_signal_rw(
                signal_type,
                write_pv=f"{prefix}{write_pv}{i + offset}",
                read_pv=f"{prefix}{read_pv}{i + offset}",
            )
            for i in range(1, no_channels + 1)
        }
    )


def create_r_device_vector(
    prefix: str,
    no_channels: int,
    read_pv: str,
    signal_type: type[SignalDatatypeT],
    zero_pv_index: bool = False,
) -> DeviceVector:
    if zero_pv_index:
        offset = -1
    else:
        offset = 0
    return DeviceVector(
        {
            i: epics_signal_r(
                signal_type,
                read_pv=f"{prefix}{read_pv}{i + offset}",
            )
            for i in range(1, no_channels + 1)
        }
    )
