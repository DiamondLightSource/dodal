import numpy as np
from scipy import signal
import matplotlib.pyplot as plt

import bluesky.plan_stubs as bps
import bluesky.plans as bp
from bluesky.protocols import Movable
from bluesky import RunEngine
from bluesky.utils import ProgressBarManager

def find_sample(start: float, stop: float, n_steps: int,
                 motor: Movable, detectors, exposure: float = 0.1, plot: bool = False):

    #setup necessities to do bluesky stuff

    RE = RunEngine({})

    # create an array of steps for counts to be performed on

    step_array = np.linspace(start,stop,n_steps)

    #do the steps, take measurements

    for step in step_array:

        yield from bps.mv(motor, step)

    summed_frames = "something"


    # find the position where there is maximum intensity using a peak fit
    # must be a 1d array containing the summed intensity of each frame
    peak_indices, properties = signal.find_peaks(summed_frames)

    if len(peak_indices) == 0:
        print("No peaks in range, retuning to start try a different range")
        end_position = start

    elif len(peak_indices) == 1:
        maximum_peak_index = peak_indices[0]
        max_peak_position = step_array[maximum_peak_index]
        end_position = max_peak_position
    elif len(peak_indices) > 1:
        maximum_peak_index = np.argmax(properties["prominences"]) #find the BIGGEST peak
        max_peak_position = step_array[maximum_peak_index]
        end_position = max_peak_position

    # move the motor to the 'sample centre' position based on the maximum 
    # intensity measured 

    if plot:
        #plot a nice graph for the user to check their results
        plt.plot(step_array,summed_frames)
        plt.plot(peak_indices, step_array[peak_indices], "x")
        plt.vlines(x=peak_indices, ymin=x[peak_indices] - properties["prominences"],
                ymax = step_array[peak_indices], color = "C1")
        plt.hlines(y=properties["width_heights"], xmin=properties["left_ips"],

                xmax=properties["right_ips"], color = "C1")
        plt.show()

    
    yield from bps.mv(motor, end_position)


