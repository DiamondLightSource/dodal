class WarningException(Exception):
    """An exception used when we want to warn an external service
    of a problem, without necesserily halting the program altogether.
    For example, GDA catches this exception from Hyperion and continues with
    UDC"""

    pass
