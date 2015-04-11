# -*- coding: utf8 -*-
"""
Tools for working with JVM ClassFiles (`.class`)
"""
__all__ = ('ClassFile', 'ClassVersion')
from struct import pack, unpack
from collections import namedtuple


from jawa.constants import ConstantPool
from jawa.fields import FieldTable
from jawa.methods import MethodTable
from jawa.attribute import AttributeTable
from jawa.util.flags import Flags


class ClassVersion(namedtuple('ClassVersion', ['major', 'minor'])):
    """
    Specifies a specific JVM version targetted by an assembled ClassFile.
    """
    __slots__ = ()

    @property
    def human(self):
        """
        A human-readable string identifying the version if known.

        For example, a ClassVersion with a major version identifier of 0x2E
        would return "JDK1_2". A ClassVersion with a major version identifier
        of 0x10 would return `None` since it's an unknown version.
        """
        return {
            0x33: 'J2SE_7',
            0x32: 'J2SE_6',
            0x31: 'J2SE_5',
            0x30: 'JDK1_4',
            0x2F: 'JDK1_3',
            0x2E: 'JDK1_2',
            0x2D: 'JDK1_1',
        }.get(self.major, None)


class ClassFile(object):
    # pylint:disable=too-many-instance-attributes
    """
    Implements the JVM ClassFile (files typically ending in `.class`).

    To open an existing ClassFile::

        from jawa import ClassFile
        with open('HelloWorld.class') as fin:
            cf = ClassFile(fin)

    To save a newly created or modified ClassFile::

        with open('HelloWorld.class', 'wb') as fout:
            cf.save(fout)

    To create a new ClassFile, use the helper :meth:`~ClassFile.create`::

        from jawa import ClassFile
        cf = ClassFile.create('HelloWorld')
        with open('HelloWorld.class', 'wb') as fout:
            cf.save(fout)

    :param fio: any file-like object providing ``.read()``.
    """
    #: The JVM ClassFile magic number.
    MAGIC = 0xCAFEBABE

    def __init__(self, fio=None):
        # Default to J2SE_7
        self.version = ClassVersion(0x32, 0)
        self.constants = ConstantPool()
        self.access_flags = Flags('>H', {
            'acc_public': 0x0001,
            'acc_final': 0x0010,
            'acc_super': 0x0020,
            'acc_interface': 0x0200,
            'acc_abstract': 0x0400,
            'acc_synthetic': 0x1000,
            'acc_annotation': 0x2000,
            'acc_enum': 0x4000
        })
        self.this = 0
        self.super_ = 0
        self.interfaces = []
        self.fields = FieldTable(self)
        self.methods = MethodTable(self)
        self.attributes = AttributeTable(self)

        if fio:
            self._from_io(fio)

    @classmethod
    def create(cls, this, super_='java/lang/Object'):
        """
        A utility method which sets up reasonable defaults.

        This method returns a ClassFile instance identical to this
        equivelent Java:

        .. code-block:: java

            public class HelloWorld extends java.lang.Object{
            }

        :param this: The name of this class.
        :param super_: The name of this class's superclass.
        """
        class_file = ClassFile()
        class_file.access_flags.acc_public = True
        class_file.access_flags.acc_super = True
        class_file.this = class_file.constants.class_(this).index
        class_file.super_ = class_file.constants.class_(super_).index

        return class_file

    def save(self, fout):
        """
        Saves the class to the file-like object `fout`.
        """
        write = fout.write

        write(pack(
            '>IHH',
            ClassFile.MAGIC,
            self.version.minor,
            self.version.major
        ))

        self.constants._to_io(fout)

        write(self.access_flags.pack())
        write(pack(
            '>HHH{0}H'.format(len(self.interfaces)),
            self.this,
            self.super_,
            len(self.interfaces),
            *self.interfaces
        ))

        self.fields._to_io(fout)
        self.methods._to_io(fout)
        self.attributes._to_io(fout)

    def _from_io(self, fio):
        """
        Loads an existing JVM ClassFile from any file-like object.
        """
        read = fio.read

        if unpack('>I', fio.read(4))[0] != ClassFile.MAGIC:
            raise ValueError('invalid magic number')

        # The version is swapped on disk to (minor, major), so swap it back.
        self.version = unpack('>HH', fio.read(4))[::-1]

        self.constants._from_io(fio)

        # ClassFile access_flags, see section #4.1 of the JVM specs.
        self.access_flags.unpack(read(2))

        # The CONSTANT_Class indexes for "this" class and its superclass.
        # Interfaces are a simple list of CONSTANT_Class indexes.
        self.this, self.super_, interfaces_count = unpack('>HHH', read(6))
        self._interfaces = unpack(
            '>{0}H'.format(interfaces_count),
            read(2 * interfaces_count)
        )

        self.fields._from_io(fio)
        self.methods._from_io(fio)
        self.attributes._from_io(fio)
