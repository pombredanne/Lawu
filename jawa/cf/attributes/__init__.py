# -*- coding: utf-8 -*-
from base64 import b64decode


class Attribute(object):
    def __init__(self, cf, name_index):
        self.cf = cf
        self.name_index = name_index

    @property
    def name(self):
        return self.cf.constants[self.name_index].value

    def __repr__(self):
        return '<Attribute({name})>'.format(
            name=self.name
        )


class UnknownAttribute(Attribute):
    def __init__(self, cf, name_index, info):
        super(UnknownAttribute, self).__init__(cf, name_index)
        self.info = info


def get_attribute(cf, name_index, info):
    info = b64decode(info)

    return Attribute(cf, name_index)
