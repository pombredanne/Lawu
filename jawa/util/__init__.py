# -*- coding: utf-8 -*-
__all__ = (
    'classes_from_paths'
)

from zipfile import is_zipfile

from jawa.jf import JarFile
from jawa.cf import ClassFile


def classes_from_paths(paths):
    """
    Takes an iterable of filesystem paths and yields any contained
    :py:class:`jawa.cf.ClassFile`.

    :param paths: Iterable of filesystem paths.
    """
    # TODO: Recursively search filesystem directories for .class
    #       files.
    for path_ in paths:
        if is_zipfile(path_):
            jf = JarFile(path_)

            for __, cf in jf.classes:
                yield cf
        else:
            with open(path_, 'rb') as fobj:
                yield ClassFile(fobj)
