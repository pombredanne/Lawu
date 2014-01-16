# -*- coding: utf-8 -*-
__all__ = ('ClassFile',)
from jawa.parsing import parse_classfile
from jawa.cf.constants import CONSTANTS_BY_TAG


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

    @property
    def major_version(self):
        return self.version[0]

    @property
    def minor_version(self):
        return self.version[1]
