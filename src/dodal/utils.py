from collections import namedtuple

Point2D = namedtuple("Point2D", ["x", "y"])
Point3D = namedtuple("Point3D", ["x", "y", "z"])

def skip_connection_test():
    def wrapper(func):
        func.skip_connection = True
        return func
    return wrapper