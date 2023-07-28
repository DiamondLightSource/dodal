from dataclasses import dataclass
from typing import Callable, Optional, Final
import numpy as np
import cv2


class ArrayProcessingFunctions():
    """
    Utility class for creating array preprocessing functions (arr -> arr with no additional parameters) 
    for some common operations.
    """
    @staticmethod
    def erode(ksize: int, iterations: int) -> Callable[[np.ndarray], np.ndarray]:
        element = cv2.getStructuringElement(cv2.MORPH_RECT, (ksize, ksize))
        return lambda arr: cv2.erode(arr, element, iterations=iterations)

    @staticmethod
    def dilate(ksize: int, iterations: int) -> Callable[[np.ndarray], np.ndarray]:
        element = cv2.getStructuringElement(cv2.MORPH_RECT, (ksize, ksize))
        return lambda arr: cv2.dilate(arr, element, iterations=iterations)
    
    @staticmethod
    def _morph(ksize: int, iterations: int, morph_type: int) -> Callable[[np.ndarray], np.ndarray]:
        element = cv2.getStructuringElement(cv2.MORPH_RECT, (ksize, ksize))
        return lambda arr: cv2.morphologyEx(
            arr, morph_type, element, iterations=iterations)

    @staticmethod
    def open_morph(ksize: int, iterations: int) -> Callable[[np.ndarray], np.ndarray]:
        return ArrayProcessingFunctions._morph(ksize=ksize, iterations=iterations, morph_type=cv2.MORPH_OPEN)

    @staticmethod
    def close(ksize: int, iterations: int) -> Callable[[np.ndarray], np.ndarray]:
        return ArrayProcessingFunctions._morph(ksize=ksize, iterations=iterations, morph_type=cv2.MORPH_CLOSE)

    @staticmethod
    def gradient(ksize: int, iterations: int) -> Callable[[np.ndarray], np.ndarray]:
        return ArrayProcessingFunctions._morph(ksize=ksize, iterations=iterations, morph_type=cv2.MORPH_GRADIENT)

    @staticmethod
    def top_hat(ksize: int, iterations: int) -> Callable[[np.ndarray], np.ndarray]:
        return ArrayProcessingFunctions._morph(ksize=ksize, iterations=iterations, morph_type=cv2.MORPH_TOPHAT)

    @staticmethod
    def black_hat(ksize: int, iterations: int) -> Callable[[np.ndarray], np.ndarray]:
        return ArrayProcessingFunctions._morph(ksize=ksize, iterations=iterations, morph_type=cv2.MORPH_BLACKHAT)

    @staticmethod
    def blur(ksize: int) -> Callable[[np.ndarray], np.ndarray]:
        return lambda arr: cv2.blur(arr, ksize=(ksize, ksize))
    
    @staticmethod
    def gaussian_blur(ksize: int) -> Callable[[np.ndarray], np.ndarray]:
        # Kernel size should be odd.
        if not ksize % 2: 
            ksize += 1
        return lambda arr: cv2.GaussianBlur(arr, (ksize, ksize), 0)
    
    @staticmethod
    def median_blur(ksize: int) -> Callable[[np.ndarray], np.ndarray]:
        if not ksize % 2: 
            ksize += 1
        return lambda arr: cv2.medianBlur(arr, ksize)


# A substitute for "None" which can fit into an np.int32 array/waveform record.
# EDM plot can't handle negative integers, so best to use 0 rather than -1.
NONE_VALUE: Final[int] = 0


@dataclass
class SampleLocation():
    """
    Holder type for results from sample detection.
    """
    tip_y: Optional[int]
    tip_x: Optional[int]
    edge_top: Optional[np.ndarray]
    edge_bottom: Optional[np.ndarray]


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
                See implementations of common functions in ArrayProcessingFunctions for predefined conversions
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

        if scan_direction not in [1, -1]:
            raise ValueError("Invalid scan direction, expected +1 for left-to-right or -1 for right-to-left")
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

        # (Could do a remove_dirt step here if wanted.)

        # Find some edges.
        edge_arr = cv2.Canny(pp_arr, self.canny_upper, self.canny_lower)

        # Do a "close" image operation. (Add other options?)
        closed_arr = ArrayProcessingFunctions.close(self.close_ksize, self.close_iterations)(edge_arr)

        # Find the sample.
        return self._locate_sample(closed_arr)
    
    def _locate_sample(self, edge_arr: np.ndarray) -> SampleLocation:
        # Straight port of Tom Cobb's algorithm from the original (adOpenCV) 
        # mxSampleDetect.

        # Index into edges_arr like [y, x], not [x, y]!
        height, width = edge_arr.shape

        tip_y, tip_x = None, None

        # TODO: use np instead?
        top = [None]*width
        bottom = [None]*width

        columns = range(width)[::self.scan_direction]

        n: np.ndarray = np.transpose(np.nonzero(edge_arr))
        
        # TODO: inefficient
        for y, x in n:
            if top[x] is None:
                top[x] = y
            bottom[x] = y

        for x in columns:
            # Look for the first non-narrow region between top and bottom edges.
            if tip_x is None and top[x] is not None and abs(top[x] - bottom[x]) > self.min_tip_height:
                
                # Move backwards to where there were no edges at all...
                while top[x] is not None:
                    x += -self.scan_direction
                    if x == -1 or x == width:
                        # (In this case the sample is off the edge of the picture.)
                        break
                x += self.scan_direction # ...and forward one step. x is now at the tip.

                tip_x = x
                tip_y = int(round(0.5*(top[x] + bottom[x])))

                # Zero the edge arrays to the left (right) of the tip.
                # TODO: inefficient
                if self.scan_direction == 1:
                    top[:x] = [None for _ in range(x)]
                    bottom[:x] = [None for _ in range(x)]
                else:
                    top[x+1:] = [None for _ in range(len(columns) - x - 1)]
                    bottom[x+1:] = [None for _ in range(len(columns) - x - 1)]

        # Prepare for export to PVs.
        # TODO: inefficient
        edge_top = np.asarray(
            [NONE_VALUE if t is None else t for t in top], dtype=np.int32)
        edge_bottom = np.asarray(
            [NONE_VALUE if b is None else b for b in bottom], dtype=np.int32)
        
        if tip_y is None or tip_x is None:
            tip_y, tip_x = -1, -1

        return SampleLocation(tip_y=tip_y, tip_x=tip_x, edge_bottom=edge_bottom, edge_top=edge_top)
