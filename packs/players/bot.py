from random import choice, randint


from ..utility.identifiers import Identifier, big, small
from . import BasePlayer
from ..game import BaseGame


class Bot(BasePlayer):
    def __init__(self, name: str, level: int):
        super().__init__(name, level)
        self._max: int = BaseGame.level.get(level, [1024, 0])[0]
        self._min: int = BaseGame.level.get(level, [0, -1024])[1]
        # self._xmin = self._xmax = 0
        self._level_max = self._max
        self._level_min = self._min
        self._last: list[int] = []
        self._historie: list[Identifier] = []
        self._pendings: list[Identifier] = []
        self._max_pending = 1

    def put(self, minvalue: int, maxvalue: int):
        self._min = minvalue
        self._max = maxvalue

    def get(self):
        # print("accessed")
        if self._max == self._min:
            return self._max

        if self._min > self._max:
            self._max, self._min = self._min, self._max
        # print(f"min = {self._min} | max = {self._max}")
        try:
            returner = choice(
                tuple(set(range(self._min, self._max)).difference(self._last)))
        except IndexError:
            self.reset()
            returner = randint(self._level_min, self._level_max)
        self._last.append(returner)
        # print('finished')
        return returner

    def critical_put(self, *values: Identifier):

        # Thanks ChatGPT!
        if len(values) == 0:
            raise ValueError("Players required")
        for value in values:
            if value.player is self:
                self._historie.append(value)
            if value.was == small:
                self._min = max(self._min, value.value)
            if value.was == big:
                self._max = min(self._max, value.value)

        for history in self._historie:
            if history.was == small:
                self._min = max(self._min, history.value)
            if history.was == big:
                self._max = min(self._max, history.value)

        # print(f"max = {self._max} | min = {self._min}")

    def tell(self, *args, maxplayers=1):
        self._max_pending = maxplayers if maxplayers > 0 else 1

    def push_put(self, value: 'Identifier'):
        # print('On push put!')
        self._pendings.append(value)
        # print(f"Size push: {len(self._pendings)}")
        if self._max_pending == len(self._pendings):
            # print("Reached max pending!")
            self.do_pending()

    def do_pending(self):
        self.critical_put(*self._pendings)
        self._pendings.clear()

    def reset(self):
        self._max: int = self._level_max
        self._min: int = self._level_min

    def history(self):
        return tuple(self._last)
