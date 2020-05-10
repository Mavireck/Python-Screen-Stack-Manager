"""
I have not made any of this stuff, I only used resources from Whizse's Github:
https://github.com/whizse/exclusive-keyboard-access
And I only kept the necessary
"""

import ctypes
from time import sleep
import fcntl


_IOC_NRBITS = 8
_IOC_TYPEBITS = 8
_IOC_SIZEBITS = 14
_IOC_DIRBITS = 2

_IOC_NRMASK = (1 << _IOC_NRBITS) - 1
_IOC_TYPEMASK = (1 << _IOC_TYPEBITS) - 1
_IOC_SIZEMASK = (1 << _IOC_SIZEBITS) - 1
_IOC_DIRMASK = (1 << _IOC_DIRBITS) - 1

_IOC_NRSHIFT = 0
_IOC_TYPESHIFT = _IOC_NRSHIFT + _IOC_NRBITS
_IOC_SIZESHIFT = _IOC_TYPESHIFT + _IOC_TYPEBITS
_IOC_DIRSHIFT = _IOC_SIZESHIFT + _IOC_SIZEBITS

IOC_NONE = 0
IOC_WRITE = 1
IOC_READ = 2

def IOW(type, nr, size):
    return IOC(IOC_WRITE, type, nr, IOC_TYPECHECK(size))

def IOC_TYPECHECK(t):
    result = ctypes.sizeof(t)
    assert result <= _IOC_SIZEMASK, result
    return result

def IOC(dir, type, nr, size):
    assert dir <= _IOC_DIRMASK, dir
    assert type <= _IOC_TYPEMASK, type
    assert nr <= _IOC_NRMASK, nr
    assert size <= _IOC_SIZEMASK, size
    return (dir << _IOC_DIRSHIFT) | (type << _IOC_TYPESHIFT) | (nr << _IOC_NRSHIFT) | (size << _IOC_SIZESHIFT)


EVIOCGRAB = lambda len: IOW(ord('E'), 0x90, ctypes.c_int)

def grab():
    fcntl.ioctl(fd, EVIOCGRAB(1), True)

def ungrab():
    fcntl.ioctl(fd, EVIOCGRAB(1), False)