# -*- coding: utf-8 -*-
__all__ = (
    'parse_classfile',
)

from itertools import repeat
from struct import Struct

from jawa.errors import ParsingException


s_uint16 = Struct('>H').unpack
s_uint32 = Struct('>I').unpack
s_int16 = Struct('>h').unpack
s_int32 = Struct('>i').unpack
s_int64 = Struct('>q').unpack
s_float = Struct('>f').unpack
s_double = Struct('>d').unpack


def parse_classfile(fobj):
    """
    Parses a JVM ClassFile per the The Java Virtual Machine
    Specification, Java SE 7 Edition.

    The results of this method should be easily serialized, such
    as to JSON for a web service.

    :param fobj: Any file-like object providing `read()`.
    :rtype: dict
    """
    # NOTE: This method is the major bottleneck for almost all
    #       workflows. It has been optimized and line-by-line
    #       profiled to ensure that ConstantPool parsing is as fast
    #       as possible in pure-python, so that a search index can be
    #       quickly built. In its current form, the majority of the
    #       time is spent in read(). Unfortunately, that results
    #       in very ugly code. The original, slow version of this
    #       method was only 16 lines. </excuse>
    read = fobj.read

    if s_uint32(read(4))[0] != 0xCAFEBABE:
        raise ParsingException('bad magic value')

    cf = {
        'version': [
            # minor version
            s_uint16(read(2))[0],
            # major version
            s_uint16(read(2))[0]
        ][::-1],
        'constant_pool': [None]
    }

    constant_pool = cf['constant_pool']
    constant_pool_iter = repeat(None, s_uint16(read(2))[0] - 1)

    for __ in constant_pool_iter:
        tag = ord(read(1))

        if tag == 1:
            # CONSTANT_Utf8
            constant_pool.append((
                tag,
                read(
                    # Length prefix
                    s_uint16(read(2))[0]
                )
            ))
        elif tag == 7:
            # CONSTANT_Class
            constant_pool.append((
                tag,
                # name_index
                s_uint16(read(2))[0]
            ))
        elif tag in (9, 10, 11):
            # CONSTANT_FieldRef, CONSTANT_MethodRef, and
            # CONSTANT_InterfaceMethodRef.
            constant_pool.append((
                tag,
                # class_index
                s_uint16(read(2))[0],
                # name_and_type_index
                s_uint16(read(2))[0]
            ))
        elif tag == 8:
            # CONSTANT_String
            constant_pool.append((
                tag,
                # string_index
                s_uint16(read(2))[0]
            ))
        elif tag == 3:
            # CONSTANT_Integer
            constant_pool.append((
                tag,
                # value
                s_int32(read(4))[0]
            ))
        elif tag == 4:
            # CONSTANT_Float
            constant_pool.append((
                tag,
                # value
                s_float(read(4))[0]
            ))
        elif tag == 5:
            # CONSTANT_Long. Counts as two entries in the pool.
            constant_pool.extend((
                (
                    tag,
                    # value
                    s_int64(read(8))[0]
                ),
                # Pool padding, since CONSTANT_Long counts as
                # two items.
                None
            ))
            next(constant_pool_iter)
        elif tag == 6:
            # CONSTANT_Double. Counts as two entries in the pool.
            constant_pool.extend((
                (
                    tag,
                    # value
                    s_double(read(8))[0]
                ),
                # Pool padding, since CONSTANT_Long counts as
                # two items.
                None
            ))
            next(constant_pool_iter)
        elif tag == 12:
            # CONSTANT_NameAndType
            constant_pool.append((
                tag,
                # name_index
                s_uint16(read(2))[0],
                # descriptor_index
                s_uint16(read(2))[0]
            ))
        else:
            raise ParsingException('invalid tag type')

    return cf
