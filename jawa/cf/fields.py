# -*- coding: utf-8 -*-
__all__ = ('Field',)
from jawa.cf.attributes import get_attribute


class Field(object):
    def __init__(self, cf, access_flags, name, descriptor, attributes):
        self.cf = cf
        self.access_flags = access_flags
        self.name_index = name
        self.descriptor_index = descriptor
        self.attributes = [
            get_attribute(cf, *a) for a in attributes
        ]

    @property
    def name(self):
        return self.cf.constants[self.name_index]

    @property
    def descriptor(self):
        return self.cf.constants[self.descriptor_index]

    def __repr__(self):
        # TODO: Should show humanized access flags.
        return '<Field({descriptor!r}, {name!r})>'.format(
            descriptor=self.descriptor.value,
            name=self.name.value
        )
