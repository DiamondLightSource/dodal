def convert_percentage_to_factor(pc: float):
    """Takes a percentage value and converts it the corresponding multiplication factor.

    Args:
        pc (float): a percentage
    Returns:
        pc (float): a factor
    """
    return pc * 1e-2


def convert_factor_to_percentage(f: float):
    """Takes a multiplication factor and converts it to the corresponding percentage.

    Args:
        f (float): a factor

    Returns:
        f (float): a percentage
    """
    return f * 1e2


def convert_microns_to_cm(t_um: float):
    """Takes the numerical part of a distance in microns and converts this to cm.

    Args:
        t_um (float): a distance in microns

    Returns:
        t_um (float): a distance in cm
    """
    return t_um * 1e-4


def convert_microns_to_mm(v_um: float):
    """Takes the numerical part of a distance in microns and converts this to mm.

    Args:
        v_um (float): a distance in microns

    Returns:
        v_um (float): a distance in mm
    """
    return v_um * 1e-3


def convert_mm_to_microns(w_mm: float):
    """Takes the numerical part of a distance in mm and converts this to microns.

    Args:
        w_mm (float): a distance in mm

    Returns:
        w_um (float): a distance in microns
    """
    return w_mm * 1e3


def convert_mm_to_cm(x_mm: float):
    """Takes the numerical part of a distance in mm and converts this to cm.

    Args:
        x_mm (float): a distance in mm

    Returns:
        w_um (float): a distance in cm
    """
    return x_mm * 1e-1


def convert_cm_to_mm(y_cm: float):
    """Takes the numerical part of a distance in cm and converts this to mm.

    Args:
        y_cm (float): a distance in cm

    Returns:
        w_um (float): a distance in mm
    """
    return y_cm * 1e1


def convert_ev_to_kev(energy_ev: float):
    """Takes the numerical part of an x-ray energy in electron volts and converts this
    to keV.

    Args: energy_ev (float): a value of electron volts

    Returns:
        energy_ev (float): a value of kilo-electron volts
    """
    return energy_ev * 1e-3
