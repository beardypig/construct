"""
MPEG 4 part 12
Contributed by beardypig
"""
from construct import *

# Header box

FileTypeBox = Struct(
    "type" / Const(b"ftyp"),
    "major_brand" / String(4),
    "minor_version" / Int32ub,
    "compatible_brands" / GreedyRange(String(4)),
)

# Catch all boxes

RawBox = Struct(
    "type" / String(4, padchar=b" ", paddir="right"),
    "data" / GreedyBytes
)

FreeBox = Struct(
    "type" / Const(b"free"),
    "data" / GreedyBytes
)

SkipBox = Struct(
    "type" / Const(b"skip"),
    "data" / GreedyBytes
)

# Movie boxes, contained in a moov Box

MovieHeaderBox = Struct(
    "type" / Const(b"mvhd"),
    "version" / Int8ub,
    "flags" / Int24ub,
    Embedded(Switch(this.version, {
        1: Struct(
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

# Track boxes, contained in trak box

TrackHeaderBox = Struct(
    "type" / Const(b"tkhd"),
    "version" / Int8ub,
    "flags" / Int24ub,
    Embedded(Switch(this.version, {
        1: Struct(
            "creation_time" / Int64ub,
            "modification_time" / Int64ub,
            "track_ID" / Int32ub,
            Padding(4),
            "duration" / Int64ub,
        ),
        0: Struct(
            "creation_time" / Int32ub,
            "modification_time" / Int32ub,
            "track_ID" / Int32ub,
            Padding(4),
            "duration" / Int32ub,
        ),
    })),
    Padding(8),
    "layer" / Int16sb,
    "alternate_group" / Int16sb,
    "volume" / Int16sb,
    Padding(2),
    "matrix" / Array(9, Int32sb),
    "width" / Int32ub,
    "height" / Int32ub
)

# Movie Fragment boxes, contained in moof box

MovieFragmentHeaderBox = Struct(
    "type" / Const(b"mfhd"),
    "version" / Const(Int8ub, 0),
    "flags" / Const(Int24ub, 0),
    "sequence_number" / Int32ub
)

TrackFragmentBaseMediaDecodeTimeBox = Struct(
    "type" / Const(b"tfdt"),
    "version" / Int8ub,
    "flags" / Const(Int24ub, 0),
    "baseMediaDecodeTime" / Switch(this.version, {1: Int64ub, 0: Int32ub})
)

TrackSampleFlags = BitStruct(
    Padding(4),
    "is_leading" / BitsInteger(2),
    "sample_depends_on" / BitsInteger(2),
    "sample_is_depended_on" / BitsInteger(2),
    "sample_has_redundancy" / BitsInteger(2),
    "sample_padding_value" / BitsInteger(3),
    "sample_is_non_sync_sample" / Flag,
    "sample_degradation_priority" / BitsInteger(16),
)

TrackRunBox = Struct(
    "type" / Const(b"trun"),
    "version" / Int8ub,
    "flags" / BitStruct(
        Padding(12),
        "sample_composition_time_offsets_present" / Flag,
        "sample_flags_present" / Flag,
        "sample_size_present" / Flag,
        "sample_duration_present" / Flag,
        Padding(5),
        "first_sample_flags_present" / Flag,
        Padding(1),
        "data_offset_present" / Flag,
    ),
    "sample_count" / Int32ub,
    "data_offset" / If(this.flags.data_offset_present, Int32sb),
    "first_sample_flags" / If(this.flags.first_sample_flags_present, Int32ub),
    "sample_info" / Array(this.sample_count, Struct(
        "sample_duration" / If(this._.flags.sample_duration_present, Int32ub),
        "sample_size" / If(this._.flags.sample_size_present, Int32ub),
        "sample_flags" / If(this._.flags.sample_flags_present, TrackSampleFlags),
        "sample_composition_time_offsets" / If(
            this._.flags.sample_composition_time_offsets_present,
            IfThenElse(this._.version == 0, Int32ub, Int32sb)
        ),
    )),
)

TrackFragmentHeaderBox = Struct(
    "type" / Const(b"tfhd"),
    "version" / Int8ub,
    "flags" / BitStruct(
        Padding(6),
        "default_base_is_moof" / Flag,
        "duration_is_empty" / Flag,
        Padding(10),
        "default_sample_flags_present" / Flag,
        "default_sample_size_present" / Flag,
        "default_sample_duration_present" / Flag,
        Padding(1),
        "sample_description_index_present" / Flag,
        "base_data_offset_present" / Flag,
    ),
    "track_ID" / Int32ub,
    "base_data_offset" / If(this.flags.base_data_offset_present, Int64ub),
    "sample_description_index" / If(this.flags.sample_description_index_present, Int32ub),
    "default_sample_duration" / If(this.flags.default_sample_duration_present, Int32ub),
    "default_sample_size" / If(this.flags.default_sample_size_present, Int32ub),
    "default_sample_flags" / If(this.flags.default_sample_flags_present, TrackSampleFlags),
)

MovieExtendsHeaderBox = Struct(
    "type" / Const(b"mehd"),
    "version" / Int8ub,
    "flags" / Const(Int24ub, 0),
    "fragment_duration" / IfThenElse(this.version == 1, Int64ub, Int32ub)
)

TrackExtendsBox = Struct(
    "type" / Const(b"trex"),
    "version" / Const(Int8ub, 0),
    "flags" / Const(Int24ub, 0),
    "track_ID" / Int32ub,
    "default_sample_description_index" / Int32ub,
    "default_sample_duration" / Int32ub,
    "default_sample_size" / Int32ub,
    "default_sample_flags" / TrackSampleFlags,
)

# Movie data box

MovieDataBox = Struct(
    "type" / Const(b"mdat"),
    "data" / GreedyBytes
)

ContainerBoxLazy = LazyBound(lambda ctx: ContainerBox)

Box = Prefixed(Peek(Int32ub), Struct(
    "start" / Tell,
    "size" / Int32ub,
    "type" / Peek(String(4, padchar=b" ", paddir="right")),
    Embedded(Switch(this.type, {
        "ftyp": FileTypeBox,
        "mvhd": MovieHeaderBox,
        "moov": ContainerBoxLazy,
        "moof": ContainerBoxLazy,
        "mfhd": MovieFragmentHeaderBox,
        "tfdt": TrackFragmentBaseMediaDecodeTimeBox,
        "trun": TrackRunBox,
        "tfhd": TrackFragmentHeaderBox,
        "traf": ContainerBoxLazy,
        "mvex": ContainerBoxLazy,
        "mehd": MovieExtendsHeaderBox,
        "trex": TrackExtendsBox,
        "trak": ContainerBoxLazy,
        "tkhd": TrackHeaderBox,
        "mdat": MovieDataBox,
        "free": FreeBox,
        "skip": SkipBox,
    }, default=RawBox)),
    "end" / Tell
))

ContainerBox = Struct(
    "type" / String(4, padchar=b" ", paddir="right"),
    "children" / GreedyRange(Box),
)

MP4 = GreedyRange(Box)

__all__ = ['MP4', 'Box', 'RawBox', 'ContainerBox', 'FileTypeBox', 'FreeBox', 'MovieDataBox', 'MovieExtendsHeaderBox',
           'MovieFragmentHeaderBox', 'MovieHeaderBox', 'SkipBox', 'TrackExtendsBox',
           'TrackFragmentBaseMediaDecodeTimeBox', 'TrackFragmentHeaderBox', 'TrackHeaderBox', 'TrackRunBox']
