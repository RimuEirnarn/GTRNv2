from random import randint
from time import sleep

from . import BaseGame
from ..utility.identifiers import big, small
from ..players.bot import Bot


class SinglePlayer(BaseGame):
    def __init__(self, *players, level=5):
        super().__init__()
        self.set_level(level)
        self._players.extend(players)

    def run(self):
        smin = BaseGame.level.get(self._level, [0, -1024])[1]
        smax = BaseGame.level.get(self._level, [1024, 0])[0]
        self._mystery = randint(smin, smax)
        self._running = True
        self._turn = 0
        for player in self._players:
            player.tell(maxplayers=len(self._players))
        print(
            f"[GTRNv2] LEVEL {self._level}! Range {smin} to {smax}")
        while self._running is True:
            self._turn += 1
            if self._turn > 1:
                for _ in range(1, len(self._players)+1):
                    print("\033[1A\033[2K\r", end="")
                    print("\033[1A\033[2K\r", end="")
            print(f"Turn {self._turn}\n")
            for player in self._players:
                try:
                    player_input = player.get()
                    identifier = self.scan_value(player, player_input)
                    [_player.push_put(identifier)
                     for _player in self._players if isinstance(_player, Bot)]
                    player.state = identifier
                except KeyboardInterrupt:
                    self._running = False
                    print("Quitting the game")
            for player in self._players:
                if self._players.index(player) == 0:
                    print(f'\033[{len(self._players)-1}A', end='')
                print(
                    f"\033[2K\r{player.name}: {player.history()[-1]} {'(Too big)' if player.state.was is big else ('(Too small)' if player.state.was is small else '(Correct!)')}")
                sleep(0.1)
            sleep(2)
            if self._upheld == "stop":
                self._running = False
        print(
            f'Game ends in {self._turn} turn(s) with {len(self._winner)} winning player(s)!')
