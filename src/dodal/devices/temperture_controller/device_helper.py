from ophyd_async.core import DeviceVector, SignalDatatypeT
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw


def create_rw_device_vector(
    prefix: str,
    no_channels: int,
    write_pv: str,
    read_pv: str,
    signal_type: type[SignalDatatypeT],
    zero_pv_index: bool = False,
    single_control_channel: bool = False,
) -> DeviceVector:
    offset = -1 if zero_pv_index else 0
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
    else:
        # Create a DeviceVector with multiple channels
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
    single_control_channel: bool = False,
) -> DeviceVector:
    offset = -1 if zero_pv_index else 0

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
                    read_pv=f"{prefix}{read_pv}{i + offset}",
                )
                for i in range(1, no_channels + 1)
            }
        )
