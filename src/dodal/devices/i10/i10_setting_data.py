from enum import Enum


class I10Grating(str, Enum):
    Au400 = "400 line/mm Au"
    Si400 = "400 line/mm Si"
    Au1200 = "1200 line/mm Au"
