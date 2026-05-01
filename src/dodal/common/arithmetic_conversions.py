class Convert:
    @staticmethod
    def convert_percentage_to_factor(pc: float):
        pc = pc / 100
        return pc

    # Takes a percentage value and converts it the corresponding multiplication factor
    @staticmethod
    def convert_factor_to_percentage(f: float):
        f = f * 100
        return f

    # Takes a multiplication factor and converts it to the corresponding percentage
    @staticmethod
    def convert_microns_to_cm(t_um):
        t_um = t_um / 10000
        return t_um

    # Takes the numerical part of a distance in microns and converts this to cm
    @staticmethod
    def convert_microns_to_mm(v_um):
        v_um = v_um * 1000
        return v_um

    # Takes the numerical part of a distance in microns and converts this to mm

    @staticmethod
    def convert_mm_to_microns(w_mm):
        w_mm = w_mm / 1000
        return w_mm

    # Takes the numerical part of a distance in mm and converts this to microns

    @staticmethod
    def convert_mm_to_cm(x_mm):
        x_mm = x_mm / 10
        return x_mm

    # Takes the numerical part of a distance in mm and converts this to cm

    @staticmethod
    def convert_cm_to_mm(y_cm):
        y_cm = y_cm * 10
        return y_cm

    # Takes the numerical part of a distance in cm and converts this to mm

    @staticmethod
    def convert_ev_to_kev(energy_ev):
        energy_ev = energy_ev / 1000
        return energy_ev

    # Takes the numerical part of an x-ray energy in electron volts and converts this to keV.

    # @staticmethod
    # def is_within_range(lower_bound, upper_bound, tested_value):
    #     a = lower_bound + upper_bound + tested_value
    #     return a


# Ensures each argument is a real number and checks last argument is within the range
# #(inclusive of bound values)
