from enum import Enum

from ophyd_async.core import StandardReadable
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw

class WatsonMarlow323Enable(str, Enum):
     DISABLED = "Disabled"
     ENABLED = "Enabled"

class WatsonMarlow323Direction(str, Enum):
     CW = "CW"
     CCW = "CCW"

class WatsonMarlow323State(str, Enum):
     STOPPED = "STOP"
     STARTED = "START"

class WatsonMarlow323(StandardReadable):
     """Watson Marlow 323 Pump device"""
     def __init__(self, prefix: str, name: str= "") -> None:
          
          self.enabled = epics_signal_r(WatsonMarlow323Enable, prefix + "DISABLE")
          
          self.direction = epics_signal_rw(
               WatsonMarlow323Direction, read_pv = prefix + "INFO:DIR", write_pv= prefix + "SET:DIR"
          )     
          self.state = epics_signal_rw(
                WatsonMarlow323State, read_pv = prefix + "INFO:RUN", write_pv = prefix + "SET:RUN"
          )
          self.speed = epics_signal_rw(
               float, read_pv = prefix + "INFO:SPD",write_pv = prefix + "SET:SPD"
          )
          self.limit_high = epics_signal_rw(
               float, read_pv = prefix + "SET:SPD.DRVH", write_pv = prefix + "SET:SPD.DRVH"
          )
          self.limit_low = epics_signal_rw(
               float, read_pv = prefix + "SET:SPD.DRVL", write_pv = prefix + "SET:SPD.DRVL"
          )

          self.set_readable_signals(
               read=[
                    self.speed,
                    self.direction
               ],
               config=[
                    self.state,
                    self.limit_high,
                    self.limit_low,
                    self.enabled
               ]
          )

          super().__init__(name=name)