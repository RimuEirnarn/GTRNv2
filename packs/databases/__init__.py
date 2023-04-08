from collections import UserList
from typing import NamedTuple


class UserStat(NamedTuple):
    victories: int
    defeats: int


class UserHistory(UserList):
    def __repr__(self):
        return f"UserHistory({len(self)})"


class User(NamedTuple):
    """User model. Basically unusable for table creation"""
    uid: str
    username: str


class History(NamedTuple):
    """History model. Basically unusable for table creation"""
    id: str
    player_1: str
    player_2: str
    winner: int  # I guess it was either 0 or 1, 1 or 2, 0 or 1 or 2
    mystery: int
