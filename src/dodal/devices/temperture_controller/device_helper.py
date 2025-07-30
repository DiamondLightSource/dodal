from ophyd_async.core import DeviceVector, SignalDatatypeT
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw


def create_rw_device_vector(
    prefix: str,
    no_channels: int,
    write_pv: str,
    read_pv: str,
    signal_type: type[SignalDatatypeT],
    pv_index_offset: int = 0,
    single_control_channel: bool = False,
) -> DeviceVector:
    if single_control_channel:
        return DeviceVector(
            {
                1: epics_signal_rw(
                    signal_type,
                    write_pv=f"{prefix}{write_pv}",
                    read_pv=f"{prefix}{read_pv}",
                )
            }
        )

    return DeviceVector(
        {
            i: epics_signal_rw(
                signal_type,
                write_pv=f"{prefix}{write_pv}{i + pv_index_offset}",
                read_pv=f"{prefix}{read_pv}{i + pv_index_offset}",
            )
            for i in range(1, no_channels + 1)
        }
    )


def create_r_device_vector(
    prefix: str,
    no_channels: int,
    read_pv: str,
    signal_type: type[SignalDatatypeT],
    pv_index_offset: int = 0,
    single_control_channel: bool = False,
) -> DeviceVector:
    if single_control_channel:
        return DeviceVector(
            {
                1: epics_signal_r(
                    signal_type,
                    read_pv=f"{prefix}{read_pv}",
                )
            }
        )
    else:
        return DeviceVector(
            {
                i: epics_signal_r(
                    signal_type,
                    read_pv=f"{prefix}{read_pv}{i + pv_index_offset}",
                )
                for i in range(1, no_channels + 1)
            }
        )
