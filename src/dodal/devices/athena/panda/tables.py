from collections import deque, namedtuple

import numpy as np
from ophyd_async.panda import SeqTable

Frame = namedtuple(
    "Frame",
    (
        "repeats",
        "trigger",
        "position",
        "time1",
        "outa1",
        "outb1",
        "outc1",
        "outd1",
        "oute1",
        "outf1",
        "time2",
        "outa2",
        "outb2",
        "outc2",
        "outd2",
        "oute2",
        "outf2",
    ),
)


def table_frames(frames, width, posn=600, step=6):
    """Convert stream of individual columns into windowed chunks"""
    buffer = deque((r for _, r in zip(range(width), frames)), maxlen=width)
    for frame in frames:
        yield from as_table_frame(buffer, posn, step)
        buffer.append(frame)


def frame(
    *,
    repeats=1,
    trigger="Immediate",
    position=0,
    time1=0,
    outa1=0,
    outb1=0,
    outc1=0,
    outd1=0,
    oute1=0,
    outf1=0,
    time2=0,
    outa2=0,
    outb2=0,
    outc2=0,
    outd2=0,
    oute2=0,
    outf2=0,
) -> Frame:
    """Create frame optionally overriding default values"""
    return Frame(
        repeats,
        trigger,
        position,
        time1,
        outa1,
        outb1,
        outc1,
        outd1,
        oute1,
        outf1,
        time2,
        outa2,
        outb2,
        outc2,
        outd2,
        oute2,
        outf2,
    )


def as_table_frame(buffer, posn=600, step=6):
    """Convert a set of frame data into frames with positions and triggers"""
    yield frame(trigger="POSA>=POSITION", position=posn)
    for a, b, c, d, e, f, *_ in buffer:
        yield frame(
            trigger="POSA<=POSITION",
            position=posn,
            outa2=a,
            outb2=b,
            outc2=c,
            outd2=d,
            oute2=e,
            outf2=f,
        )
        posn -= step
        if posn <= 0:
            break
    yield frame(trigger="POSA<=POSITION", position=max(0, posn))


def table_chunks(frames, length):
    """Split stream of frames into groups that can be set as sequence tables"""
    buffer = [iter(frames)] * length
    for chunk in zip(*buffer):
        yield list(chunk) + [frame(repeats=0)]


def seq_tables(tables):
    for table in tables:
        yield build_table(*zip(*table))


def build_table(
    repeats,
    trigger,
    position,
    time1,
    outa1,
    outb1,
    outc1,
    outd1,
    oute1,
    outf1,
    time2,
    outa2,
    outb2,
    outc2,
    outd2,
    oute2,
    outf2,
):
    table = SeqTable()
    table["repeats"] = np.array(repeats, dtype=np.uint16)
    table["position"] = np.array(position, dtype=np.int32)
    table["trigger"] = np.array(trigger)
    table["time1"] = np.array(time1, np.uint32)
    table["outa1"] = np.array(outa1, np.uint8)
    table["outb1"] = np.array(outb1, np.uint8)
    table["outc1"] = np.array(outc1, np.uint8)
    table["outd1"] = np.array(outd1, np.uint8)
    table["oute1"] = np.array(oute1, np.uint8)
    table["outf1"] = np.array(outf1, np.uint8)
    table["time2"] = np.array(time2, np.uint32)
    table["outa2"] = np.array(outa2, np.uint8)
    table["outb2"] = np.array(outb2, np.uint8)
    table["outc2"] = np.array(outc2, np.uint8)
    table["outd2"] = np.array(outd2, np.uint8)
    table["oute2"] = np.array(oute2, np.uint8)
    table["outf2"] = np.array(outf2, np.uint8)
    return table
