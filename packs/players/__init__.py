"""Players"""

from typing import Any, Protocol, Sequence
from uuid import UUID
from ..utility import default_uid


class ProtoPlayer(Protocol):
    """Protocol Player"""
    _name: str
    _state: Any
    _history: list[int]

    def get_id(self) -> str | UUID | None:
        pass

    def get(self) -> int:  # type: ignore
        pass

    def put(self, minvalue: int, maxvalue: int):
        pass

    def tell(self, *args, maxplayers: int):
        pass

    def reset(self):
        pass

    @property
    def name(self) -> str:
        return self._name

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value: Any):
        self._state = value

    def history(self):
        return tuple(self._history)


class BasePlayer:
    """Base class for Player-related class."""

    def __init__(self, name: str, level: int):
        self._uid: UUID = default_uid
        self._name = name
        self._level = level
        self._history = []
        self._state = None

    def get_state(self):
        return self._state

    def get(self):
        return None

    def put(self, minvalue: int, maxvalue: int):
        pass

    def tell(self, *args: Any, maxplayers: int = 0):
        pass

    def __repr__(self):
        return f"{type(self).__name__}({self._name})"

    def get_id(self):
        return self._name if not hasattr(self, '_uid') else self._uid

    def history(self):
        return tuple(self._history)

    def reset(self):
        pass

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value: Any):
        self._state = value
