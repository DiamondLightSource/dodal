import cv2
from matplotlib.pylab import standard_t
import numpy as np
from ophyd_async.core import StandardReadable, soft_signal_r_and_setter
from bluesky.protocols import Triggerable
from ophyd_async.epics.core import (
    epics_signal_r,
)


class GetCentre(StandardReadable, Triggerable):
    def __init__(self, prefix:str, name : str = "") -> None:
        self.array_data = epics_signal_r(np.ndarray, f"pva://{prefix}PVA:ARRAY")
        self.center_pixel_x, self._x_setter = soft_signal_r_and_setter(int)
        self.center_pixel_y, self._y_setter = soft_signal_r_and_setter(int)

        pass

    async def preprocessing(self):
        """
        Creates a binary image (pixel will be either 25 or 0) using Otsu's method for automatic threshholding.
      The threshold is increased by 20 (brightness taken from image in grayscale) in order to obtain the more reliable
      inner section of the beam.
      """
        arr = await self.array_data.get_value()
        if arr is None:
            raise Exception("OAV image data not loaded.")
        gray = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        #max_pixel = np.max(blurred)
        (thresh, thresh_img) = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # adjusting because the inner beam is less noisy compared to the outer. 
        thresh = thresh + 20

        thresh_arr = cv2.threshold(blurred, thresh, 255, cv2.THRESH_BINARY)[1]

        print(f"[INFO] thresholding value (otsu with blur): {thresh}")
        return thresh_arr
    
    async def fit_ellipse(self):
        binary = await self.preprocessing()
        
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if not contours:
            raise ValueError("No contours found in image.")

        largest_contour = max(contours, key=cv2.contourArea)
        if len(largest_contour) < 5:
            raise ValueError("Not enough points to fit an ellipse.")

        return cv2.fitEllipse(largest_contour) # we can now extract x and y from here
    
    async def trigger(self):
        fit = await self.fit_ellipse()[0]
        self._x_setter(fit[0])
        self._y_setter(fit[1])
        
    







#-----------------------------------------------

def binary_img(img_path, write_img = False,  img_name = "Threshold"):
    """
    Function which creates a binary image from a beamline image using Otsu's method for automatic threshholding.
      The threshold is increased by 20 (brightness taken from image in grayscale) in order to obtain the more reliable
      inner section of the beam.
    """
    img = cv2.imread(img_path)
    if img is None: 
        raise 
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    #max_pixel = np.max(blurred)
    (T, thresh_img) = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # adjusting because the inner beam is less noisy compared to the outer. 
    
    T = T + 20

    thresh_img = cv2.threshold(blurred, T, 255, cv2.THRESH_BINARY)[1]
    if write_img:
        cv2.imwrite(f"./BinaryImages/{img_name}.jpg", thresh_img)
    print("[INFO] thresholding value (otsu with blur): {}".format(T))
    return thresh_img


# find centre using an Ellipse
class FitEllipse:
    def __init__(self, img_path: str):
        self.img_path = img_path
        self.binary = binary_img(self.img_path)
        self.ellipse = self.fit_ellipse()

    def fit_ellipse(self):
        contours, _ = cv2.findContours(self.binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if not contours:
            raise ValueError("No contours found in image.")

        largest_contour = max(contours, key=cv2.contourArea)
        if len(largest_contour) < 5:
            raise ValueError("Not enough points to fit an ellipse.")

        return cv2.fitEllipse(largest_contour)

    def center(self) -> tuple:
        return self.ellipse[0]  # (x, y)

    def draw_ellipse_and_write(self, output_path: str):
        output = cv2.cvtColor(self.binary, cv2.COLOR_GRAY2BGR)
        cv2.ellipse(output, self.ellipse, (0, 255, 0), 2)
        cv2.imwrite(output_path, output)
        print(f"Ellipse image saved to: {os.path.abspath(output_path)}")