# -*- coding: utf-8 -*-
"""
Support for parsing Attributes.
"""
__all__ = (
    'get_attribute',
    'ATTRIBUTE_MAP',
    'Attribute',
    'UnknownAttribute'
)

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from base64 import b64decode
from contextlib import closing
from itertools import repeat

from jawa.parsing import s_uint16, s_uint32, parse_attribute_table


class Attribute(object):
    """
    The base Attribute type, also used if no suitable class
    is found for a specific type of Attribute.
    """
    def __init__(self, cf, name_index, info=None):
        self.cf = cf
        self.name_index = name_index
        self.info = info

    @property
    def name(self):
        """
        The name of this attribute as defined in the ClassFile,
        such as `Code` or `ConstantValue`.
        """
        return self.cf.constants[self.name_index].value

    def __repr__(self):
        return '<Attribute({name})>'.format(
            name=self.name
        )


class ConstantValue(Attribute):
    """
    The `ConstantValue` attribute, as defined in section 4.7.2 of the
    Java SE 7 Edition specification.
    """
    def __init__(self, cf, name_index, info):
        super(ConstantValue, self).__init__(cf, name_index)
        self.constantvalue_index = s_uint16(info[:2])[0]

    @property
    def constantvalue(self):
        """
        The :py:class:`~jawa.cf.constant.Constant` object which
        contains the actual value.
        """
        return self.cf.constants[self.constantvalue_index]

    def __repr__(self):
        return '<ConstantValue({value!r})>'.format(
            value=self.constantvalue
        )


class Code(Attribute):
    """
    The `Code` attribute, as defined in section 4.7.3 of the Java SE
    7 Edition specification.

    This is the "meat" of a typical class, and contains the bodies
    of most methods.
    """
    def __init__(self, cf, name_index, info):
        super(Code, self).__init__(cf, name_index)

        fobj = StringIO(info)
        read = fobj.read

        with closing(fobj):
            self.max_stack = s_uint16(read(2))[0]
            self.max_locals = s_uint16(read(2))[0]
            self.code = read(
                # code_length
                s_uint32(read(4))[0]
            )

            exception_table_length = s_uint16(read(2))[0]
            self.exception_table = [
                (
                    # start_pc
                    s_uint16(read(2))[0],
                    # end_pc
                    s_uint16(read(2))[0],
                    # handler_pc
                    s_uint16(read(2))[0],
                    # catch_type
                    s_uint16(read(2))[0]
                )
                for __ in repeat(None, exception_table_length)
            ]

            self.attributes = [
                get_attribute(cf, *a)
                for a in parse_attribute_table(fobj)
            ]

    def __repr__(self):
        return '<Code({length} bytes)>'.format(
            length=len(self.code)
        )


#: A map of known and supported attributes, from their name to the
#: class implementing it.
ATTRIBUTE_MAP = {
    'ConstantValue': ConstantValue,
    'Code': Code
}


def get_attribute(cf, name_index, info):
    """
    Given the ConstantPool index of an attributes name and it's
    data as `info`, returns an :py:class:`Attribute` subclass
    which parses it. If no class can be found, a generic attribute
    is returned.

    .. note::

        This is a convenience function used when loading a ClassFile
        and its interface may change.

    :param cf: The :py:class:`~jawa.cf.ClassFile` that owns the
               attribute being parsed.
    :param name_index: An index into the ConstantPool which contains
                       the name of the attribute being parsed.
    :param info: The raw, base64-encoded content of the attribute
                 being parsed.
    :rtype: :py:class:`Attribute`
    :returns: A parsed Attribute.
    """
    info = b64decode(info)

    return ATTRIBUTE_MAP.get(
        cf.constants[name_index].value,
        Attribute
    )(cf, name_index, info)
