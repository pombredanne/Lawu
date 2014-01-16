# -*- coding: utf-8 -*-
"""
Convienient representations of entries in the Constant Pool.
"""
__all__ = (
    'Constant',
    'Utf8',
    'Integer',
    'Float',
    'Long',
    'Double',
    'Class',
    'String',
    'FieldRef',
    'MethodRef',
    'InterfaceMethodRef',
    'NameAndType',
    'CONSTANTS_BY_TAG'
)


class Constant(object):
    def __init__(self, cf):
        self.cf = cf


class ValueConstant(Constant):
    def __init__(self, cf, value):
        super(ValueConstant, self).__init__(cf)
        self.value = value

    def __repr__(self):
        return '<{name}({value})>'.format(
            name=self.__class__.__name__,
            value=self.value
        )


class Utf8(ValueConstant):
    def __repr__(self):
        return '<Utf8({length} bytes)>'.format(
            length=len(self.value)
        )


class Integer(ValueConstant):
    pass


class Float(ValueConstant):
    pass


class Long(ValueConstant):
    pass


class Double(ValueConstant):
    pass


class Class(Constant):
    def __init__(self, cf, name_index):
        super(Class, self).__init__(cf)
        self.name_index = name_index

    @property
    def name(self):
        return self.cf.constants[self.name_index]

    def __repr__(self):
        return '<Class({name!r})>'.format(
            name=self.name.value
        )


class String(Constant):
    def __init__(self, cf, string_index):
        super(String, self).__init__(cf)
        self.string_index = string_index


class FieldRef(Constant):
    def __init__(self, cf, class_index, name_and_type_index):
        super(FieldRef, self).__init__(cf)
        self.class_index = class_index
        self.name_and_type_index = name_and_type_index


class MethodRef(Constant):
    def __init__(self, cf, class_index, name_and_type_index):
        super(MethodRef, self).__init__(cf)
        self.class_index = class_index
        self.name_and_type_index = name_and_type_index


class InterfaceMethodRef(Constant):
    def __init__(self, cf, class_index, name_and_type_index):
        super(InterfaceMethodRef, self).__init__(cf)
        self.class_index = class_index
        self.name_and_type_index = name_and_type_index


class NameAndType(Constant):
    def __init__(self, cf, name_index, descriptor_index):
        super(NameAndType, self).__init__(cf)
        self.name_index = name_index
        self.descriptor_index = descriptor_index


#: A list containing all the Constant Pool types, ordered by the
#: value of their 'tag'. This can be used for quick type lookups
#: when parsing.
CONSTANTS_BY_TAG = [
    None,
    Utf8,
    None,
    Integer,
    Float,
    Long,
    Double,
    Class,
    String,
    FieldRef,
    MethodRef,
    InterfaceMethodRef,
    NameAndType
]
