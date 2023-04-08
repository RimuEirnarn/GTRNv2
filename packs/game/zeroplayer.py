from random import randint
from time import sleep

from . import BaseGame
from ..utility.identifiers import big, small
from ..players.bot import Bot


class ZeroPlayer(BaseGame):
    def __init__(self, bots: int = 0, level: int = 5):
        super().__init__()
        self.set_level(level)
        self._players.append(Bot("Bot-0", self._level))
        if bots > 1:
            for a in range(1, bots):
                self._players.append(Bot(f"Bot-{a}", self._level))

    def run(self):
        smin = BaseGame.level.get(self._level, [0, -1024])[1]
        smax = BaseGame.level.get(self._level, [1024, 0])[0]
        self._mystery = randint(smin, smax)
        self._running = True
        self._turn = 0
        for player in self._players:
            if isinstance(player, Bot):
                player.tell(maxplayers=len(self._players))
        print(
            f"""Mystery Number: {self._mystery} (level {self._level})\nRanging from: {smin} to {smax}""")
        while self._running is True:
            self._turn += 1
            print(f"Turn {self._turn}")
            for player in self._players:
                try:
                    player_input = player.get()
                    identifier = self.scan_value(player, player_input)
                    print(
                        f"{player.name}: {player_input} {'(Too big)' if identifier.was is big else ('(Too small)' if identifier.was is small else 'Correct!')}")
                    [_player.push_put(identifier)
                     for _player in self._players if isinstance(_player, Bot)]
                    sleep(0.01)
                except KeyboardInterrupt:
                    try:
                        input("Interrupted.")
                    except KeyboardInterrupt:
                        self._running = False
                        break
            print()
            if self._upheld == "stop":
                self._running = False
        print(
            f'Game ends in {self._turn} turn(s) with {len(self._winner)} winning player(s)!')
