def calculate(num: float, multiplier: float):
    return num * multiplier


def convert_percentage_to_factor(pc: float):
    # Takes a percentage value and converts it the corresponding multiplication factor
    return calculate(pc, 1e-2)


def convert_factor_to_percentage(f: float):
    # Takes a multiplication factor and converts it to the corresponding percentage
    return calculate(f, 1e2)


def convert_microns_to_cm(t_um: float):
    # Takes the numerical part of a distance in microns and converts this to cm
    return calculate(t_um, 1e-4)


def convert_microns_to_mm(v_um: float):
    # Takes the numerical part of a distance in microns and converts this to mm
    return calculate(v_um, 1e-3)


def convert_mm_to_microns(w_mm: float):
    # Takes the numerical part of a distance in mm and converts this to microns
    return calculate(w_mm, 1e3)


def convert_mm_to_cm(x_mm: float):
    # Takes the numerical part of a distance in mm and converts this to cm
    return calculate(x_mm, 1e-1)


def convert_cm_to_mm(y_cm: float):
    # Takes the numerical part of a distance in cm and converts this to mm
    return calculate(y_cm, 1e1)


def convert_ev_to_kev(energy_ev: float):
    # Takes the numerical part of an x-ray energy in electron volts and converts this to
    # keV.
    return calculate(energy_ev, 1e-3)
