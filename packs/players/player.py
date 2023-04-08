from . import BasePlayer


class Player(BasePlayer):
    def __init__(self, name: str):
        super().__init__(name, 0)

    def get(self):
        try:
            x = int(input("\033[2KYour input: "))
            self._history.append(x)
            return x
        except (Exception, KeyboardInterrupt) as exc:
            print('')
            self._history.append(None)
        return 0
