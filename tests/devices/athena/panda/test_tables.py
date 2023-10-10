from dodal.devices.athena.panda.tables import table_chunks, table_frames

testframes = iter(
    [
        (0, 0, 0, 0, 0, 0),
        (0, 0, 1, 1, 0, 0),
        (0, 1, 0, 0, 1, 0),
        (0, 1, 0, 0, 1, 0),
        (0, 0, 1, 0, 1, 0),
        (0, 1, 1, 1, 1, 0),
        (0, 0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0, 0),
        (0, 1, 1, 1, 1, 1),
        (0, 1, 0, 0, 1, 0),
        (0, 1, 0, 0, 1, 0),
        (0, 1, 0, 0, 1, 0),
        (0, 0, 1, 1, 0, 0),
        (0, 0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0, 0),
        (0, 0, 1, 1, 0, 0),
        (0, 1, 0, 0, 1, 0),
        (0, 1, 0, 0, 1, 0),
        (0, 1, 0, 0, 1, 0),
        (0, 0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0, 0),
    ]
)


def test_table_chunks():
    tc = table_chunks(range(100), 12)
    first = next(tc)
    assert len(first) == 13


def test_table_frames():
    tf = table_frames(testframes, 12)
    full = list(tf)
    print(full[1])
    print(full[14])
    for i in range(12):
        left = full[i + 1]
        right = full[i + 14]
        assert left.outa2 == right.outa2
        assert left.outb2 == right.outb2
        assert left.outc2 == right.outc2
        assert left.outd2 == right.outd2
        assert left.oute2 == right.oute2
        assert left.outf2 == right.outf2
