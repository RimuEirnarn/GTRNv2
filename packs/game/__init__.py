from typing import Any, Protocol


from ..utility.errors import RedefineIsRequired
from ..utility.identifiers import Identifier, big, small, equal
from ..databases.game import GameDB
from ..players import ProtoPlayer


class ProtoGame(Protocol):

    def register_player(self, player: Any):
        pass

    def set_level(self, level: int):
        pass

    def run(self):
        pass

    def start(self):
        pass

    def reset(self):
        pass


class BaseGame:
    _instance = {}
    level: dict[int, tuple[int, int]] = {i: (2**v, -2**v)
                                         for i, v in enumerate(range(5, 106))}

    def __new__(cls, *args, **kwargs):
        if cls in BaseGame._instance:
            return BaseGame._instance[cls]
        self = super().__new__(cls)
        cls._instance[cls] = self
        return self

    def __init__(self):
        self._players: list[ProtoPlayer] = []
        self._mystery = None
        self._running = False
        self._database = GameDB()
        self._level = 0
        self._turn = 0
        self._winner = []
        self._upheld = "none"

    def register_player(self, player: Any):
        if self._running is True:
            return
        self._players.append(player)

    def scan_value(self, player: 'ProtoPlayer', value: int):
        if self._mystery is None:
            raise Exception("Mystery number is missing")
        if value == self._mystery:
            self._winner.append(player)
            self._upheld = "stop"
        return Identifier(player, big if value > self._mystery else (equal if self._mystery == value else small), value)

    def set_level(self, level):
        if self._running is True:
            return
        self._level = level if isinstance(level, int) else 0

    def run(self):
        """Re-define this method on your new class.

        Example:
        while self._running is True:
            <your code>
        """
        RedefineIsRequired().warn()
        from time import sleep
        timed = 5
        self._running = True
        while self._running is True:
            print(f"Game will ends in {timed}")
            if timed == 0:
                self._running = False
                break
            timed -= 1
            sleep(1)

    def start(self):
        self.run()
        self.reset()

    def reset(self):
        self._mystery = None
        self._upheld = "stop"
        self._winner.clear()
        self._turn = 0
        for p in self._players:
            p.reset()

    @property
    def isRunning(self):
        return self._running

    @property
    def Level(self):
        return self._level

    def __repr__(self):
        return f"<{type(self).__name__} State={self._upheld} Players={len(self._players)} Running={self._running}>"
