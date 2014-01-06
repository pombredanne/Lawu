# -*- coding: utf-8 -*-
__all__ = (
    'parse_classfile',
    'ParseMode'
)

from base64 import b64encode
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


class ParseMode(object):
    PARSE_ALL = 10
    #: Stop parsing the ClassFile after the ConstantPool.
    PARSE_CONSTANTS = 20
    #: Stop parsing the ClassFile after the interface list.
    PARSE_INTERFACES = 30
    #: Stop parsing the ClassFile after the fields list.
    PARSE_FIELDS = 40
    #: Stop parsing the ClassFile after the methods list.
    PARSE_METHODS = 50


def parse_attribute_table(fobj):
    read = fobj.read

    attributes_count = s_uint16(read(2))[0]

    for __ in repeat(None, attributes_count):
        yield (
            # attribute_name_index
            s_uint16(read(2))[0],
            # info
            b64encode(read(
                # attribute_length
                s_uint32(read(4))[0]
            ))
        )


def parse_classfile(fobj, parse_mode=ParseMode.PARSE_ALL):
    """
    Parses a JVM ClassFile per the The Java Virtual Machine
    Specification, Java SE 7 Edition.

    The results of this method should be easily serialized, such
    as to JSON for a web service.

    :param fobj: Any file-like object providing `read()`.
    :param parse_mode: How much of the file should be parsed before
                       returning.
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

    if parse_mode == ParseMode.PARSE_CONSTANTS:
        # When building a quick search index, typically all that's
        # needed is the ConstantPool.
        return cf

    cf['access_flags'] = s_uint16(read(2))[0]
    cf['this_class'] = s_uint16(read(2))[0]
    cf['super_class'] = s_uint16(read(2))[0]

    # Interfaces are simply a length-prefix list of ConstantPool
    # indexes, where the indexed value is a CONSTANT_Class.
    cf['interfaces'] = [
        s_uint16(read(2))[0]
        for __ in repeat(None, s_uint16(read(2))[0])
    ]

    if parse_mode == ParseMode.PARSE_INTERFACES:
        return cf

    ###
    # Parse the fields table.
    ###
    fields_count = s_uint16(read(2))[0]
    cf['fields'] = [
        (
            # access_flags
            s_uint16(read(2))[0],
            # name_index
            s_uint16(read(2))[0],
            # descriptor_index
            s_uint16(read(2))[0],
            list(parse_attribute_table(fobj))
        )
        for __ in repeat(None, fields_count)
    ]

    if parse_mode == ParseMode.PARSE_FIELDS:
        return cf

    ###
    # Parse the methods table.
    ###
    methods_count = s_uint16(read(2))[0]
    cf['methods'] = [
        (
            # access_flags
            s_uint16(read(2))[0],
            # name_index
            s_uint16(read(2))[0],
            # descriptor_index
            s_uint16(read(2))[0],
            list(parse_attribute_table(fobj))
        )
        for __ in repeat(None, methods_count)
    ]

    if parse_mode == ParseMode.PARSE_METHODS:
        return cf

    cf['attributes'] = list(parse_attribute_table(fobj))

    return cf
