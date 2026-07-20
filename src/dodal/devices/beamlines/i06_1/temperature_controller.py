# from ophyd_async.core import (
#     SignalR,
#     SignalRW,
#     StandardReadableFormat,
#     StrictEnum,
# )
# from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

# from dodal.devices.temperature_controller import (
#     PID,
#     BaseHeater,
#     BaseTemperatureSensor,
#     TemperatureController,
# )


# class CryoconM32Sensor(BaseTemperatureSensor):
#     def __init__(
#         self,
#         prefix: str,
#         name: str = "",
#     ):

#         with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
#             self.temperature = epics_signal_r(float, prefix + "STS:T1")
#             self._sensor_2 = epics_signal_r(float, prefix + "STS:T2")
#         with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
#             self.sensor_min = epics_signal_r(float, prefix + "STS:T1:MIN")
#             self.sensor_max = epics_signal_r(float, prefix + "STS:T1:MAX")
#             self.sensor_slope = epics_signal_r(float, prefix + "STS:T1:SLOPE")
#             self.sensor_offset = epics_signal_r(float, prefix + "STS:T1:OFFSET")
#             self.sensor2_min = epics_signal_r(float, prefix + "STS:T2:MIN")
#             self.sensor2_max = epics_signal_r(float, prefix + "STS:T2:MAX")
#             self.sensor2_slope = epics_signal_r(float, prefix + "STS:T2:SLOPE")
#             self.sensor2_offset = epics_signal_r(float, prefix + "STS:T2:OFFSET")

#         super().__init__(name=name)
