from dataclasses import dataclass

from ..players import ProtoPlayer
from . import Symbol


@dataclass(init=True, repr=False)
class Identifier:
    player: ProtoPlayer
    was: Symbol
    value: int

    def __eq__(self, other):
        return self.value == other.value

    def __gt__(self, other):
        return self.value > other.value

    def __ge__(self, other):
        return self.value >= other.value

    def __lt__(self, other):
        return self.value < other.value

    def __le__(self, other):
        return self.value <= other.value

    def __repr__(self):
        return f"Identifier({self.player._name}, {self.was}, {self.value})"


def _always_false(x): return False
def _always_true(x): return True


big = Symbol('big', 'bigger', lt_hook=_always_false,
             le_hook=_always_false, gt_hook=_always_true, ge_hook=_always_false)
small = Symbol('small', 'smaller', lt_hook=_always_true,
               le_hook=_always_true, gt_hook=_always_false, ge_hook=_always_false)
equal = Symbol('equal', "equal", lt_hook=_always_false,
               le_hook=_always_true, gt_hook=_always_false, ge_hook=_always_true)
