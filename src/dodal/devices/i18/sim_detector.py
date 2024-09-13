from ophyd_async.epics.motor import Motor
from ophyd_async.sim.demo import PatternGenerator


class SimDetector:
    def __init__(self, name: str, motor: Motor, motor_field: str):
        self.name = name
        self.motor = motor
        self.motor_field = motor_field
        self.pattern_generator = PatternGenerator(
            saturation_exposure_time=0.1, detector_height=100, detector_width=100
        )

    def read(self):
        return {self.name: {"value": self.pattern_generator}}

    def describe(self):
        return {self.name: {"source": "synthetic", "dtype": "number"}}
