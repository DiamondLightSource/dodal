from dataclasses import dataclass
from enum import Enum
from typing import Callable, Final, Optional, Tuple

import cv2
import numpy as np

from dodal.log import LOGGER


class ScanDirections(Enum):
    FORWARD = 1
    REVERSE = -1


def identity(*args, **kwargs) -> Callable[[np.ndarray], np.ndarray]:
    return lambda arr: arr


def erode(ksize: int, iterations: int) -> Callable[[np.ndarray], np.ndarray]:
    element = cv2.getStructuringElement(cv2.MORPH_RECT, (ksize, ksize))
    return lambda arr: cv2.erode(arr, element, iterations=iterations)


def dilate(ksize: int, iterations: int) -> Callable[[np.ndarray], np.ndarray]:
    element = cv2.getStructuringElement(cv2.MORPH_RECT, (ksize, ksize))
    return lambda arr: cv2.dilate(arr, element, iterations=iterations)


def _morph(
    ksize: int, iterations: int, morph_type: int
) -> Callable[[np.ndarray], np.ndarray]:
    element = cv2.getStructuringElement(cv2.MORPH_RECT, (ksize, ksize))
    return lambda arr: cv2.morphologyEx(arr, morph_type, element, iterations=iterations)


def open_morph(ksize: int, iterations: int) -> Callable[[np.ndarray], np.ndarray]:
    return _morph(ksize=ksize, iterations=iterations, morph_type=cv2.MORPH_OPEN)


def close(ksize: int, iterations: int) -> Callable[[np.ndarray], np.ndarray]:
    return _morph(ksize=ksize, iterations=iterations, morph_type=cv2.MORPH_CLOSE)


def gradient(ksize: int, iterations: int) -> Callable[[np.ndarray], np.ndarray]:
    return _morph(ksize=ksize, iterations=iterations, morph_type=cv2.MORPH_GRADIENT)


def top_hat(ksize: int, iterations: int) -> Callable[[np.ndarray], np.ndarray]:
    return _morph(ksize=ksize, iterations=iterations, morph_type=cv2.MORPH_TOPHAT)


def black_hat(ksize: int, iterations: int) -> Callable[[np.ndarray], np.ndarray]:
    return _morph(ksize=ksize, iterations=iterations, morph_type=cv2.MORPH_BLACKHAT)


def blur(ksize: int, *args, **kwargs) -> Callable[[np.ndarray], np.ndarray]:
    return lambda arr: cv2.blur(arr, ksize=(ksize, ksize))


def gaussian_blur(ksize: int, *args, **kwargs) -> Callable[[np.ndarray], np.ndarray]:
    # Kernel size should be odd.
    if not ksize % 2:
        ksize += 1
    return lambda arr: cv2.GaussianBlur(arr, (ksize, ksize), 0)


def median_blur(ksize: int, *args, **kwargs) -> Callable[[np.ndarray], np.ndarray]:
    if not ksize % 2:
        ksize += 1
    return lambda arr: cv2.medianBlur(arr, ksize)


ARRAY_PROCESSING_FUNCTIONS_MAP = {
    0: erode,
    1: dilate,
    2: open_morph,
    3: close,
    4: gradient,
    5: top_hat,
    6: black_hat,
    7: blur,
    8: gaussian_blur,
    9: median_blur,
    10: identity,
}


# A substitute for "None" which can fit into an numpy int array.
# Also used as a substitute for a not-found sample position.
NONE_VALUE: Final[int] = -1


@dataclass
class SampleLocation:
    """
    Holder type for results from sample detection.
    """

    tip_y: Optional[int]
    tip_x: Optional[int]
    edge_top: np.ndarray
    edge_bottom: np.ndarray


class MxSampleDetect(object):
    def __init__(
        self,
        *,
        preprocess: Callable[[np.ndarray], np.ndarray] = lambda arr: arr,
        canny_upper: int = 100,
        canny_lower: int = 50,
        close_ksize: int = 5,
        close_iterations: int = 5,
        scan_direction: int = 1,
        min_tip_height: int = 5,
    ):
        """
        Configures sample detection parameters.

        Args:
            preprocess: A preprocessing function applied to the array after conversion to grayscale.
                See implementations of common functions above for predefined conversions
                Defaults to a no-op (i.e. no preprocessing)
            canny_upper: upper threshold for canny edge detection
            canny_lower: lower threshold for canny edge detection
            close_ksize: kernel size for "close" operation
            close_iterations: number of iterations for "close" operation
            scan_direction: +1 for left-to-right, -1 for right-to-left
            min_tip_height: minimum height of pin tip
        """

        self.preprocess = preprocess
        self.canny_upper = canny_upper
        self.canny_lower = canny_lower
        self.close_ksize = close_ksize
        self.close_iterations = close_iterations

        if scan_direction not in [
            ScanDirections.FORWARD.value,
            ScanDirections.REVERSE.value,
        ]:
            raise ValueError(
                "Invalid scan direction, expected +1 for left-to-right or -1 for right-to-left"
            )
        self.scan_direction = scan_direction

        self.min_tip_height = min_tip_height

    def processArray(self, arr: np.ndarray) -> SampleLocation:
        # Get a greyscale version of the input.
        if arr.ndim == 3:
            gray_arr = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
        else:
            assert arr.ndim == 2
            gray_arr = arr

        # Preprocess the array. (Use the greyscale one.)
        pp_arr = self.preprocess(gray_arr)

        # Find some edges.
        edge_arr = cv2.Canny(pp_arr, self.canny_upper, self.canny_lower)

        closed_arr = close(self.close_ksize, self.close_iterations)(edge_arr)

        # Find the sample.
        return self._locate_sample(closed_arr)

    @staticmethod
    def _first_and_last_nonzero_by_columns(
        arr: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Finds the indexes of the first & last non-zero values by column in a 2d array.

        Outputs will contain NONE_VALUE if no non-zero values exist in a column.

        i.e. for input:
        [
            [0, 0, 0, 1],
            [1, 1, 0, 0],
            [0, 1, 0, 1],
        ]

        first_nonzero will be: [1, 1, NONE_VALUE, 0]
        last_nonzero will be [1, 2, NONE_VALUE, 2]
        """
        nonzero = arr.astype(dtype=bool, copy=False)
        any_nonzero_in_column = nonzero.any(axis=0)

        first_nonzero = np.where(
            any_nonzero_in_column, nonzero.argmax(axis=0), NONE_VALUE
        )

        flipped = nonzero.shape[0] - np.flip(nonzero, axis=0).argmax(axis=0) - 1
        last_nonzero = np.where(any_nonzero_in_column, flipped, NONE_VALUE)

        return first_nonzero, last_nonzero

    def _locate_sample(self, edge_arr: np.ndarray) -> SampleLocation:
        height, width = edge_arr.shape

        top, bottom = MxSampleDetect._first_and_last_nonzero_by_columns(edge_arr)

        # Calculate widths. In general if bottom == top this has width 1.
        # special case for bottom == top == NONE_VALUE (i.e. no edge at all), that has width 0.
        widths = np.where(top != NONE_VALUE, bottom - top + 1, 0)

        # Generate the indices of columns with widths larger than the specified min tip height.
        non_narrow_widths = widths >= self.min_tip_height
        column_indices_with_non_narrow_widths = np.flatnonzero(non_narrow_widths)

        if column_indices_with_non_narrow_widths.shape[0] == 0:
            # No non-narrow locations - sample not in picture?
            # Or wrong parameters for edge-finding, ...
            LOGGER.warning(
                "pin-tip detection: No non-narrow edges found - cannot locate pin tip"
            )
            return SampleLocation(
                tip_y=None, tip_x=None, edge_bottom=bottom, edge_top=top
            )

        # Choose our starting point - i.e. first column with non-narrow width for positive scan, last one for negative scan.
        if self.scan_direction == ScanDirections.FORWARD.value:
            start_column = int(column_indices_with_non_narrow_widths[0])
        else:
            start_column = int(column_indices_with_non_narrow_widths[-1])

        x = start_column

        # Move backwards to where there were no edges at all...
        while top[x] != NONE_VALUE:
            x += -self.scan_direction
            if x == -1 or x == width:
                # (In this case the sample is off the edge of the picture.)
                LOGGER.warning(
                    "pin-tip detection: Pin tip may be outside image area - assuming at edge."
                )
                break
        x += self.scan_direction  # ...and forward one step. x is now at the tip.

        tip_x = x
        tip_y = int(round(0.5 * (top[x] + bottom[x])))

        # clear edges to the left (right) of the tip.
        if self.scan_direction == 1:
            top[:x] = NONE_VALUE
            bottom[:x] = NONE_VALUE
        else:
            top[x + 1 :] = NONE_VALUE
            bottom[x + 1 :] = NONE_VALUE

        LOGGER.info(
            "pin-tip detection: Successfully located pin tip at (x={}, y={})".format(
                tip_x, tip_y
            )
        )
        return SampleLocation(
            tip_y=tip_y, tip_x=tip_x, edge_bottom=bottom, edge_top=top
        )
