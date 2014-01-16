# -*- coding: utf-8 -*-
__all__ = ('ClassFile',)
from jawa.parsing import parse_classfile
from jawa.cf.constants import CONSTANTS_BY_TAG
from jawa.cf.fields import Field
from jawa.cf.methods import Method
from jawa.cf.attributes import get_attribute


class ClassFile(object):
    def __init__(self, fobj):
        cf = parse_classfile(fobj)

        self.version = cf['version']
        self.constants = constants = []

        for constant in cf['constant_pool']:
            if constant is None:
                # We need to keep the None entries around. They pad
                # the pool so that indexes are correct.
                constants.append(None)
                continue

            constants.append(CONSTANTS_BY_TAG[
                constant[0]
            ](self, *constant[1:]))

        self.access_flags = cf['access_flags']

        self.this_class_index = cf['this_class']
        self.super_class_index = cf['super_class']

        self.interfaces = [
            self.constants[i] for i in cf['interfaces']
        ]

        self.fields = [Field(self, *f) for f in cf['fields']]
        self.methods = [Method(self, *m) for m in cf['methods']]
        self.attributes = [
            get_attribute(self, *a) for a in cf['attributes']
        ]

    @property
    def major_version(self):
        return self.version[0]

    @property
    def minor_version(self):
        return self.version[1]

    @property
    def this_class(self):
        return self.constants[self.this_class_index]

    @property
    def super_class(self):
        return self.constants[self.super_class_index]
