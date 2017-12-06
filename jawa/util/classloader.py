# -*- coding: utf-8 -*-
import os
import os.path
from itertools import izip, repeat
from zipfile import ZipFile
from collections import OrderedDict

from jawa.cf import ClassFile


def _walk(path, follow_links=False, maximum_depth=None):
    """A modified os.walk with support for maximum traversal depth."""
    root_level = path.rstrip(os.path.sep).count(os.path.sep)
    for root, dirs, files in os.walk(path, followlinks=follow_links):
        yield root, dirs, files
        if maximum_depth is None:
            continue

        if root_level + maximum_depth <= root.count(os.path.sep):
            del dirs[:]


class ClassLoader(object):
    """Emulate the Java ClassPath.

    Provides utilities for managing a java classpath as well as loading
    classes from those paths.

    :param follow_symlinks: True if symlinks should be followed when traversing
                            filesystem directories. [default: False]
    :type follow_symlinks: True
    :param maximum_depth: The maximum sub-directory depth when traversing
                          filesystem directories. If set to `None` no limit
                          will be enforced. [default: 20]
    :type maximum_depth: Long or None.
    :param max_cache: The maximum number of ClassFile's to store in the cache.
                      If set to 0, no classes with be cached. [default: 50]
    :type max_cache: Long
    """
    def __init__(self, follow_symlinks=False, maximum_depth=20, max_cache=50):
        self.path_map = {}
        self.follow_symlinks = follow_symlinks
        self.maximum_depth = maximum_depth
        self.class_cache = OrderedDict()
        self.max_cache = max_cache

    def add_path(self, *paths):
        """Add a new path to the class loader.

        If the given `path` is a directory, it is traversed up to the maximum
        set depth and all files under it are added to the class loader lookup
        table.

        If the given `path` is a .jar or .zip file it will be opened and the
        file index added to the class loader lookup table.

        :param paths: Any number of paths to either a ZIP/JAR or a directory to
                      be added to the classpath.
        :type paths: unicode
        """
        for path in paths:
            # We're adding an archive to the classpath so we want to open it,
            # get the index, and unpack it into our path map.
            if path.lower().endswith(('.zip', '.jar')):
                with ZipFile(path, 'r') as zf:
                    self.path_map.update(izip(zf.namelist(), repeat(path)))
                    return
            elif os.path.isdir(path):
                walker = _walk(
                    path,
                    follow_links=self.follow_symlinks,
                    maximum_depth=self.maximum_depth
                )
                for root, dirs, files in walker:
                    for file_ in files:
                        path_full = os.path.join(root, file_)
                        path_suffix = os.path.relpath(path_full, path)
                        self.path_map[path_suffix] = path_full

    def load(self, path):
        """Load the class at `path` or return an asset path.

        If `path` points to a valid fully-qualified class it will be loaded
        and returned.

        :param path: Fully-qualified path to a ClassFile or an asset file.
        :type path: unicode
        """
        try:
            full_path = self.path_map[path]
        except KeyError as original_e:
            try:
                full_path = self.path_map[path + '.class']
            except KeyError:
                raise original_e
            else:
                path = path + '.class'

        try:
            r = self.class_cache.pop(path)
        except KeyError:
            if full_path.endswith(('.zip', '.jar')):
                with ZipFile(full_path, 'r') as zf:
                    with zf.open(path) as fio:
                        r = ClassFile(fio)
            else:
                with open(full_path, 'rb') as fio:
                    r = ClassFile(fio)

        self.class_cache[path] = r

        # If the cache is enabled removed every item over N started from
        # the least-used.
        if self.max_cache > 0:
            to_pop = max(len(self.class_cache) - self.max_cache, 0)
            for _ in repeat(None, to_pop):
                self.class_cache.popitem(last=False)

        return r

    def clear(self):
        """Erase all stored paths and all cached classes."""
        self.path_map.clear()
        self.class_cache.clear()
