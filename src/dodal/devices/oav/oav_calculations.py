import numpy as np


def camera_coordinates_to_xyz_mm(
    horizontal: float,
    vertical: float,
    omega: float,
    microns_per_i_pixel: float,
    microns_per_j_pixel: float,
) -> np.ndarray:
    """
    Converts from (horizontal,vertical) pixel measurements from the OAV camera into to (x, y, z) motor coordinates in millimetres.
    For an overview of the coordinate system for I03 see https://github.com/DiamondLightSource/hyperion/wiki/Gridscan-Coordinate-System.

    Args:
        horizontal (float): A i value from the camera in pixels.
        vertical (float): A j value from the camera in pixels.
        omega (float): The omega angle of the smargon that the horizontal, vertical measurements were obtained at.
        microns_per_i_pixel (float): The number of microns per i pixel, adjusted for the zoom level horizontal was measured at.
        microns_per_j_pixel (float): The number of microns per j pixel, adjusted for the zoom level vertical was measured at.
    """
    # Convert the vertical and horizontal into mm.
    horizontal *= microns_per_i_pixel * 1e-3
    vertical *= microns_per_j_pixel * 1e-3

    # +ve x in the OAV camera becomes -ve x in the smargon motors.
    x = -horizontal

    # Rotating the camera causes the position on the vertical horizontal to change by raising or lowering the centre.
    # We can negate this change by multiplying sin and cosine of the omega.
    radians = np.radians(omega)
    cosine = np.cos(radians)
    sine = np.sin(radians)

    # +ve y in the OAV camera becomes -ve y in the smargon motors/
    y = -vertical * cosine

    z = vertical * sine
    return np.array([x, y, z], dtype=np.float64)


def calculate_beam_distance(
    beam_centre: tuple[int, int],
    horizontal_pixels: int,
    vertical_pixels: int,
) -> tuple[int, int]:
    """
    Calculates the distance between the beam centre and the given (horizontal, vertical).

    Args:
        horizontal_pixels (int): The x (camera coordinates) value in pixels.
        vertical_pixels (int): The y (camera coordinates) value in pixels.
    Returns:
        The distance between the beam centre and the (horizontal, vertical) point in pixels as a tuple
        (horizontal_distance, vertical_distance).
    """
    beam_x, beam_y = beam_centre
    return (
        beam_x - horizontal_pixels,
        beam_y - vertical_pixels,
    )
