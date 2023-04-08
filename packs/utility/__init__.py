"""Utility library for GTRNv2

This library/module only contain utilities that the core library needs but no need to write those utility.
In the nutshell, generalised utilities.

There's no need to import PATH from lib when there's generalised library."""

import os
from base64 import b64decode, b64encode
from io import FileIO
from platform import system
from threading import Event
from typing import Any, Callable, Dict, Literal, Union
from urllib.parse import urlsplit
from uuid import UUID, uuid1, uuid5

from .errors import AssignedProtocolError
from .symbol import Symbol

# Pre-constants

MODE = Literal['rb', 'r', 'wb', 'w']


# =================================================================

#                           Helper function

# =================================================================

def _check_prefix(d: str):
    try:
        prefix, part, suffix = d.partition("://")
    except Exception:
        return False
    return True


# =================================================================

#                            Helper Class

# =================================================================


# Constants
default = Symbol('default', object())
_default = Symbol("default", None)
default_uid = UUID(int=0)

# =========

# =========================================================================

#                            Utility Classes

# =========================================================================


class Protocol:
    """Base Protocol class handler."""
    _prefix = {}

    def __init_subclass__(cls, /, prefix, final=True):
        if prefix in Protocol._prefix:
            raise AssignedProtocolError(f"{prefix} is already assigned")

        def finaliser(self):
            raise NotImplementedError
        Protocol._prefix[prefix] = cls
        if final is True:
            cls.__init_subclass__ = finaliser  # type: ignore

    def __new__(cls, url: str):
        prefix, _, path = url.partition("://")
        if prefix in cls._prefix:
            x = super().__new__(cls._prefix[prefix])
            return x
        return super().__new__(cls)

    def __init__(self, url: str):
        self._url = url
        self._splitted = urlsplit(url)
        self._path = url.partition("://")[2]

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self._url}>"


class Project(Protocol, prefix='project'):
    def read_path(self):
        path = getpath()
        if path[-1] == '/':
            return path[:-1]+self._path
        elif self._path[0] != '/':  # project://foo.bar
            return path+'/'+self._path  # /home/foo/.config/GTRNv2/foo.bar
            # ! /home/foo/.config/GTRNv2foo.bar
        return path+self._path

    def __str__(self) -> str:
        return self.read_path()


class ConfigProtocol(Protocol, prefix='config'):
    def __init__(self, url: str, accept_mapping: bool = True):
        self._url = url
        self._base = url.partition("://")[2]
        if self._base[0] == '/':
            raise ValueError(
                "Failed to get config key. Eliminated by third slash.")
        self._config_name = self._base.split('/')[0]
        self._lpath_config = self._base.split('/')[1:]
        self._path_config = '/'.join(self._lpath_config)
        l = [(str(a[0]), a[1])
             for a in tuple(Configuration._instances.items())]
        self._config = None
        self._mapping = accept_mapping
        for v in l:
            if self._config_name == v[0]:
                self._config = v[1]
        if self._config is None:
            raise FileNotFoundError(
                f"[{self._config_name}] No such 'file' or 'directory'.")

    def get(self):
        if self._config is None:
            raise ValueError("Configuration is undefined")
        left_object = self._config
        left_key = None
        index = 0
        raise_ = False
        if len(self._lpath_config) == 0:
            raise ValueError("Path to variable is needed.")
        for a in self._lpath_config:
            if raise_ is True:
                _2left = self._lpath_config[index - 2] \
                    if not index <= 1 else \
                    self._config_name

                raise ValueError(
                    f"While iterating on {left_key} from {_2left}, we found {a} in url while {left_key} seems not a mapping-like object. (We actually want to return {left_key} but instead found {a})")
            if self._mapping:
                if not hasattr(left_object, '__getitem__'):
                    raise_ = True
                if a in left_object:
                    left_object: Configuration = left_object[a]
                    left_key = a
            else:
                if isinstance(left_object, Configuration):
                    if a in left_object:
                        left_object = left_object[a]
                        left_key = a
            index += 1
        return left_object


class Configuration:
    """Configuration class

    By default, this configuration class creates singleton object but not as always.
    Change the reference or ref, you can have new(?) singleton object.

    This config class also provides backup. You can do commit() or rollback()
    Note that you can't access the backup from __getattr__.

    For convenience, you can use something like x[key] to access the data without touching with object's properties.
    Also, you can set a data even if it's violating naming conventions such as whitespaces.

    >>> x['A Random Key'] = None
    >>> x.A Random Key
    SyntaxError: invalid syntax
    >>> x['A Random Key']
    >>> x._name
    # some random name
    >>> x['_name'] = 'Some config'
    >>> x._name == x['_name']
    False
    """
    _instances: Dict[Symbol, 'Configuration'] = {}

    def __contains__(self, __name: str):
        return self._data.__contains__(__name)

    def __new__(cls, ref: Symbol | Any = _default, __data: dict | None = None, **kwargs):
        if ref in Configuration._instances:
            return Configuration._instances[ref]

        self = super().__new__(cls)
        Configuration._instances[ref] = self
        # self.__init__(ref, __data, **kwargs)
        return self

    def __init__(self, ref: Symbol | Any = _default, __data: dict | None = None, **kwargs):
        if not isinstance(ref, Symbol):
            ref = Symbol(f'Reference[{type(ref)}]', ref)
        if ref._value == "GameConfig":
            prev = True

            def expander(data: Any | str):
                if not _check_prefix(data):
                    return data
                try:
                    return expandproject(data)
                except Exception:
                    return data

            def update_hook(data: dict[str, Union[str, Any]]):  # type: ignore
                x = {}
                for k, v in data.items():
                    x[k] = expander(v)
                return x

        else:
            prev = False

            def expander(data: Union[Any, str]):
                return data

            def update_hook(data: Dict[str, Any]):
                return data

        self._nowritebase = False
        self._data = {}
        self._backup = {}
        self._frozen = Event()
        self._name = ref._value
        self._ref = ref
        self._hook = expander
        if __data is not None:
            self._data.update(update_hook(__data))
        else:
            self._data.update(update_hook(kwargs))
        if prev is True:
            self._unhooked_data = __data or kwargs.copy()
        else:
            self._unhooked_data = {}
        self._backup.update(self._data)
        self.__dict__['_ref'] = ref
        self._nowritebase = True

    def __repr__(self):
        return f"Configuration(%s)" % self._name

    def __call__(self):
        return self._data if self._frozen.is_set() is False else self._data.copy()

    def __getattr__(self, __name):
        """Implement getattr(name)."""
        if __name in self.__dict__:
            return self.__dict__[__name]
        return self.__dict__['_data'][__name]

    def __setattr__(self, __name: Any, __value: Any):
        """Implement setattr(name, value)."""
        if __name == '_nowritebase':
            self.__dict__[__name] = __value  # type: ignore
            return
        if self.__dict__.get("_nowritebase", False) is False:
            if not "_hook" in self.__dict__:
                return super().__setattr__(__name, __value)  # type: ignore

            if not "_frozen" in self.__dict__:
                return super().__setattr__(__name, self._hook(__value))  # type: ignore

            if self._frozen.is_set():
                return
            super().__setattr__(__name, self._hook(__value))  # type: ignore
        else:
            self._data[__name] = self._hook(__value)

    def __getitem__(self, __key: str):
        """x.__getitem__(y) <==> x[y]"""
        return self._data[__key]

    def __setitem__(self, __key: Any, __value: Any):
        """Set self[key] to value."""
        if '_hook' in self.__dict__:
            self._data[__key] = self._hook(__value)
        else:
            self._data[__key] = __value

    def __delitem__(self, __key: str):
        """Delete self[key]."""
        del self._data[__key]

    def __update__(self, __new_data: dict | None = None, **kwargs):
        """Update attributes of this object with a new data or kwargs."""
        if __new_data is not None:
            return self._data.update(__new_data)
        self._data.update(kwargs)

    update = __update__

    def switch_ro(self):
        """Change the state of the writability of this singleton object."""
        if self._frozen.is_set():
            return self._frozen.clear()
        self._frozen.set()

    def install_hook(self, func: Callable):
        """Install a hook into this object (called on setattr)"""
        self._nowritebase = False
        setattr(self, '_hook', func) if getattr(
            self, '_name') != "GameConfig" else None

        def update_hook(data: Dict[str, Any]) -> Dict[str, Any]:
            x = {}
            for k, v in data.items():
                x[k] = func(v)
            return x
        setattr(self, '_update_hook', update_hook) if getattr(
            self, '_name') != "GameConfig" else None
        self._nowritebase = True

    def commit(self):
        """Commit changes and save the change to backup (cannot be rollbacked again)"""
        self._backup.clear()
        self._backup.update(self._data)

    def rollback(self):
        """Rollback changes to previous save (or init)"""
        self._data.clear()
        self._data.update(self._backup)

    def listall(self, moderef=0):
        """List all members/variables inside a certain data."""
        if moderef == 0:
            return tuple(self._data.keys())
        elif moderef == 1:
            return tuple(self._backup.keys())
        elif moderef == 2:
            return tuple(self.__dict__.keys())
        else:
            return self.listall()


class Base64IO(FileIO):
    def __init__(self, filename, mode: MODE):
        super().__init__(filename, mode)
        self._mode = mode

    def read(self, __size: int | None = None) -> Union[str, bytes]:
        x = super().read(__size if __size else 0)
        if isinstance(x, str):
            x = x.encode('utf-8')
        x = b64decode(x, b'-_')
        if 'b' in self._mode:
            return x
        return x.decode('utf-8')

    def write(self, buffer: Union[str, bytes]) -> int:
        x = buffer if isinstance(buffer, bytes) else buffer.encode('utf-8')
        if 'b' in self._mode:
            return super().write(b64encode(x, b'-_'))
        return super().write(b64encode(x, b'-_'))

    def _raw_read(self, __size: int) -> Union[str, bytes]:
        return super().read(__size)

    def _raw_write(self, buffer: Union[str, bytes]) -> int:
        if isinstance(buffer, str):
            buffer = buffer.encode('utf-8')
        return super().write(buffer)


# =================================================================

#                         Utility Functions

# =================================================================


def getpath():
    """Get the project's path (or installation path)"""
    if system() == 'Linux':
        return os.path.expanduser("~/.config/GTRNv2")
    elif system() == "Windows":
        return os.path.expanduser("~/AppData/Local/GTRNv2")
    else:
        return os.path.expanduser("~/.GTRNv2")


def touch(file):
    """Make a file without any content."""
    try:
        with open(file, 'w') as f:
            pass
    except Exception as exc:
        pass


def expandproject(url: str) -> str:
    """Expand a url to absolute path of project files.
    >>> expandproject('project:///foo.bar')
    '/home/foo/.config/GTRNv2/foo.bar'"""
    path = getpath()
    prefix, part, suffix = url.partition('://')
    del part
    if prefix != "project":
        raise ValueError("Undefined protocol/prefix: %s" % prefix)
    if path[-1] != '/' and suffix[0] == '/':
        return path+suffix
    if path[-1] == '/' and suffix[0] == '/':
        return path[:-1]+suffix
    if path[-1] != '/' and suffix[0] != '/':
        return path+'/'+suffix
    if path[-1] == '/' and suffix[0] != '/':
        return path+suffix
    return path+suffix


def install():
    """Install project directory into project path."""
    # install
    # Folder structure:
    #           /
    # game.db  plugin/ downloads/ crash/ logs/
    path = getpath()
    os.makedirs(f'{path}/plugin', 0o700, True)
    os.makedirs(f'{path}/downloads', 0o700, True)
    os.makedirs(f'{path}/logs', 0o700, True)
    os.makedirs(f'{path}/crash', 0o700, True)
    return True


def make_uid(name: str):
    n = uuid1()
    return uuid5(n, name)


__all__ = ['Symbol', 'Configuration', 'default',
           'getpath', 'touch', 'install', 'expandproject']
__version__ = "0.0.0 [02]"
__author__ = "RimuEirnarn"
__copyright__ = "BSD 3-Clause License"
