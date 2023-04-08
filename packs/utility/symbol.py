from ast import parse as _astparse
from inspect import currentframe
from inspect import getframeinfo
from typing import Any

from .typings import OpHook


class Symbol:
    """Symbol

    This class marks a certain name as symbol's name (or flag) and store a value.
    when doing:
    >>> x, y = Symbol('Hello'), Symbol("Hello")
    >>> x is y
    will return True"""
    _sym = {}

    def __new__(cls, name: str | None = None, value: Any | None = None, /, *args, **kwargs):
        if name is None and value is None:  # This shit is copied from RPGSample/libshared.py
            current_frame = currentframe()
            if current_frame is None:
                raise ValueError("Cannot get current frame")
            back_frame = current_frame.f_back
            if back_frame is None:
                raise ValueError("Cannot get back frame")
            caller = getframeinfo(back_frame)  # Don't edit this part.
            if caller.index is None:
                raise ValueError("Cannot get caller index")
            if caller.code_context is not None:
                code = _astparse(caller.code_context[caller.index])
                name = code.body[0].targets[0].id  # type: ignore
                value = f"Ref[{caller.function}.{name}]"
            else:
                code = None
                name = f'Constant-{len(cls._sym)}'
                value = f"Ref[{name}]"
            del caller, code
        if name in cls._sym:
            return cls._sym[name]
        self = super().__new__(cls)
        Symbol._sym[name] = self
        return self

    def __init__(self,
                 name: str | None = None,
                 value: Any | None = None,
                 /,
                 lt_hook: OpHook | None = None,
                 le_hook: OpHook | None = None,
                 gt_hook: OpHook | None = None,
                 ge_hook: OpHook | None = None):
        if name is None and value is None:  # This shit is copied from RPGSample/libshared.py
            current_frame = currentframe()
            if current_frame is None:
                raise ValueError("Cannot get current frame")
            back_frame = current_frame.f_back
            if back_frame is None:
                raise ValueError("Cannot get back frame")
            caller = getframeinfo(back_frame)  # Don't edit this part.
            if caller.index is None:
                raise ValueError("Cannot get caller index")
            if caller.code_context is not None:
                code = _astparse(caller.code_context[caller.index])
                name = code.body[0].targets[0].id  # type: ignore
                value = f"Ref[{caller.function}.{name}]"
            else:
                code = None
                name = f'Constant-{len(self._sym)}'
                value = f"Ref[{name}]"
            del caller, code
        self._name = name
        self._value = value
        self._type = type(value)
        self._default_hook = lambda other: False
        self._hooks = {
            'lt': lt_hook or self._default_hook,
            'le': le_hook or self._default_hook,
            'gt': gt_hook or self._default_hook,
            'ge': ge_hook or self._default_hook
        }

    def __str__(self):
        if self._type is not str:
            return NotImplemented
        return self._value

    def __int__(self):
        """Return int(self)."""
        if self._type is not int:
            return NotImplemented
        return self._value

    def __float__(self):
        """Return float(self)."""
        if self._type is not float:
            return NotImplemented
        return self._value

    def __gt__(self, other):
        return self._hooks['gt'](other)

    def __le__(self, other):
        return self._hooks['le'](other)

    def __lt__(self, other):
        return self._hooks['lt'](other)

    def __ge__(self, other):
        return self._hooks['ge'](other)

    def __repr__(self):
        return f"Symbol(%s)" % self._name
