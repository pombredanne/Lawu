# -*- coding: utf-8 -*-
import zipfile as zf

from jawa.cf import ClassFile


class JarFile(zf.ZipFile):
    @property
    def classes(self):
        for zi in self.infolist():
            if zi.filename.endswith('.class'):
                yield zi, ClassFile(self.open(zi))
