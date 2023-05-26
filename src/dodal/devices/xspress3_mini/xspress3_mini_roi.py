from ophyd import Device


class Xspress3MiniROI(Device):
    prefix = "-EA-XSP3-01"
    total_rois = 0

    def __init__(self):
        Xspress3MiniROI.total_rois += 1
        self.this_roi_number = Xspress3MiniROI.total_rois
