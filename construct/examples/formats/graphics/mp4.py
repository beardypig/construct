"""
MPEG 4 part 12
Contributed by beardypig
"""
from construct import *


def sizeof_box(ctx):
    if hasattr(ctx, "children"):
        return 8 + sum(map(sizeof_box, ctx.children))
    else:
        return ctx.size


class ChildBoxConstruct(RepeatUntil):
    def __init__(self):
        super(ChildBoxConstruct, self).__init__(lambda obj,ctx: obj.end == ctx._.start + ctx._.size, Box)

    def _build(self, obj, stream, context, path):
        try:
            super(ChildBoxConstruct, self)._build(obj, stream, context, path)
        except RangeError:
            # ignore the range error
            pass


RawBox = Struct(
    "type" / String(4, padchar=b" ", paddir="right"),
    "offset" / Tell,
    "data" / RawCopy(Bytes(this._.size - this.offset + this._.start)),
)

FileTypeBox = Struct(
    "type" / Const(b"ftyp"),
    "major_brand" / String(4),
    "minor_version" / String(4),
    "offset" / Tell,
    "compatible_brands" / Array((this._.size - this.offset + this._.start) // 4, String(4)),
)

MovieHeaderBox = Struct(
    "type" / Const(b"mvhd"),
    "version" / Int8ub,
    "flags" / Int24ub,
    Embedded(Switch(this.version,
        {1: Struct(
            "creation_time" / Int64ub,
            "modification_time" / Int64ub,
            "timescale" / Int32ub,
            "duration" / Int64ub,
        ),
        0: Struct(
            "creation_time" / Int32ub,
            "modification_time" / Int32ub,
            "timescale" / Int32ub,
            "duration" / Int32ub,
        ),
        })),
    "rate" / Int32sb,
    "volume" / Int16sb,
    # below could be just Padding(10) but why not
    Const(Int16ub, 0),
    Const(Int32ub, 0),
    Const(Int32ub, 0),
    "matrix" / Int32sb[9],
    "pre_defined" / Int32ub[6],
    "next_track_ID" / Int32ub,
)

MovieFragmentHeaderBox = Struct(
    "type" / Const(b"mfhd"),
    "version" / Const(Int8ub, 0),
    "flags" / Const(Int24ub, 0),
    "sequence_number" / Int32ub,
)

ContainerBoxLazy = LazyBound(lambda ctx: ContainerBox)

Box = Struct(
    "start" / Tell,
    "size" / Rebuild(Int32ub, sizeof_box),
    "type" / Peek(String(4, padchar=b" ", paddir="right")),
    Embedded(Switch(this.type, {
        "ftyp": FileTypeBox,
        "mvhd": MovieHeaderBox,
        "moov": ContainerBoxLazy,
        "moof": ContainerBoxLazy,
        "mfhd": MovieFragmentHeaderBox,
        "traf": ContainerBoxLazy
        }, default=RawBox)),
    "end" / Tell,
)

ContainerBox = Struct(
    "type" / String(4, padchar=b" ", paddir="right"),
    "children" / ChildBoxConstruct(),
)

MP4 = GreedyRange(Box)

