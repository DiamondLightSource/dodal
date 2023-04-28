def A1():
    pass


def A2():
    pass


def A3():
    pass


def O1():
    pass


def O2():
    pass


def O3():
    pass


def some_plan():
    pass


def arming(arming=[A1, A2, A3], other=[O1, O2, O3]):
    for action in arming:
        yield from some_plan(action, 1, "A")

    for action in other:
        yield from some_plan(action, 1, "B")
