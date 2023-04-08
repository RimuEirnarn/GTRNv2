"""Game database"""

from typing import Generator, Self
from uuid import UUID

from sqlite_database import Database, integer, op, text

from ..config import GameConfig
from ..utility import make_uid
from . import History, User
from .errors import HistoryNotExists, UserNotExists
from .typings import UID


class GameDB:
    """Game database"""
    _instance = None

    def __init_subclass__(cls) -> None:
        raise Exception("This class cannot be subclassed.")

    def __new__(cls) -> 'GameDB' | Self:
        if cls._instance is not None:
            return cls._instance

        self = super(GameDB, cls).__new__(cls)
        cls._instance = self
        return self

    def __initdb__(self):
        # make_table(self._db, 'users', Value('uid', string, primary_key), Value(
        #     'username', string), Value('statistic', string), Value('history_ids', string))
        # make_table(self._db, 'history', Value('id', integer, primary_key), Value(
        #     'uid0', string), Value('uid1', string), Value('winner', integer), Value('mystery', integer))
        # self.add_user('debug')
        self._users = self._db.create_table("users", [
            text("uid").primary(),
            text("username"),
        ])
        self._history = self._db.create_table("history", [
            integer('id'),
            text("player_1").foreign("users/uid"),
            text("player_2").foreign("users/uid"),
            integer("winner"),
            integer("mystery")
        ])
        # users.insert({
        #     "uid": str(UUID(int=0)),
        #     "username": "debug"
        # })
        self.add_user("debug")

    def __init__(self):
        if GameConfig.IsDebug is True:
            self._db = Database(":memory:")
            self.__initdb__()
        else:
            self._db = Database(GameConfig.DataPath)
            if not self._db.check_table("users"):
                self.__initdb__()
        self._users = self._db.table("users")
        self._history = self._db.table("history")

    def add_user(self, username: str) -> UUID:
        """Add user"""
        uid = make_uid(username)
        stuid = str(uid)
        # self._db.execute(f"insert into users values (?, ?, ?, ?)",
        #                  (stuid, username, '0$0', '[]'))
        # self._db.commit()
        self._users.insert({
            "uid": stuid,
            "username": username
        })
        return uid

    def remove_user(self, uid: UID):
        """Remove user"""
        stuid = uid if isinstance(uid, str) else str(uid)
        # self._db.execute('delete from users where uid=:uid', {"uid": stuid})
        self._users.delete_one({
            "uid": op == stuid
        })

    def mod_user(self,
                 uid: UID,
                 username: str | None = None,
                 statistic: str | None = None,
                 history_list: str | None = None):
        """Modify user's data"""
        if sum((bool(username), bool(statistic), bool(history_list))) == 0:
            raise Exception("Nothing is edited.")
        stuid = uid if isinstance(uid, str) else str(uid)
        # injected = ''
        updates = {}
        if username:
            #     injected += 'username=:username, '
            updates['username'] = username
        if statistic:
            #     injected += 'statistic=:statistic, '
            updates['statistic'] = statistic
        if history_list:
            #     injected += 'history_ids=:history_ids, '
            updates['history_ids'] = history_list
        # const = f'update users set {injected[:-2]} where uid=:uid'
        # self._db.execute(const, key)
        return self._users.update_one(updates, {
            'uid': op == stuid
        })

    def remove_history(self):
        """Remove history"""
        # truncate_table(self._db, 'history')
        self._history = self._db.reset_table('history', [
            integer('id'),
            text("player_1").foreign("users/uid"),
            text("player_2").foreign("users/uid"),
            integer("winner"),
            integer("mystery")
        ])

    def reset(self):
        # """Reset the database"""
        # truncate_table(self._db, "users")
        # truncate_table(self._db, 'history')
        # self.add_user('debug')
        self._db.delete_table('users')
        self._db.delete_table('history')
        self.__initdb__()

    def mod_settings(self, **kwargs):
        """Change game config"""
        GameConfig.update(kwargs)

    def get_user(self, uid: UID) -> User:
        # self._force_no()
        stuid = uid if isinstance(uid, str) else str(uid)
        user = self._users.select_one({
            "uid": op == stuid
        })
        if user:
            return User(user.uid, user.username)

        raise UserNotExists("No such user.")
        # cur = self._db.execute(
        #     "select uid, username, statistic, history_ids from users where uid=:uid", {'uid': stuid})
        # if GameConfig.SQLConfig.ExpensiveTask is True:
        #     c = cur.fetchone()
        #     _a = UUID(c[0])
        #     _b = c[1]
        #     _c = c[2].split('$')
        #     _d = UserStat(_b[0], _b[2])
        #     _e = UserHistory(loads(c[-1]))
        #     return User(_a, _b, _c, c[2], _e)
        # elif GameConfig.SQLConfig.ChangeInner is False:
        #     c = cur.fetchone()
        #     return User(c[0], c[1], UserStat(*c[2].split('$')), c[2], c[3])
        # return cur.fetchone()
        Users

    def get_history_data(self, histid: int | str) -> History:
        # self._force_no()
        if isinstance(histid, str):
            if not histid.isnumeric():
                raise ValueError("History id is not an integer")
            histid = int(histid)
        history = self._history.select_one({
            "id": histid
        })
        if history:
            return History(history.id, history.player_1, history.player_2, history.winner, history.mystery)

        raise HistoryNotExists("No such history id")
        # if hasattr(histid, 'isnumeric'):
        #     if histid.isnumeric() is False:
        #         raise ValueError("History id is not an integer")
        # sthist = str(histid) if isinstance(histid, int) else histid
        # cur = self._db.execute(
        #     'select id, uid0, uid1, winner, mystery from history where id=:id', {'id': sthist})
        # if GameConfig.SQLConfig.ExpensiveTask is True:
        #     c = cur.fetchone()
        #     a, u0, u1, w, m = c
        #     u0 = self.get_user(u0)
        #     u1 = self.get_user(u1)
        #     return History(a, u0, u1, w, m)
        # elif GameConfig.SQLConfig.ChangeInner is False:
        #     return History(*cur.fetchone())
        # return cur.fetchone()

    def add_history(self, histid: int | str, player1: UID, player2: UID, winner: int, mystery: int):
        # self._force_no()
        stuid0 = player1 if isinstance(player1, str) else str(player1)
        stuid1 = player2 if isinstance(player2, str) else str(player2)
        if isinstance(histid, str):
            if not histid.isnumeric():
                raise ValueError("history id is not an integer")
            histid = int(histid)
        self._history.insert({
            "id": histid,
            "player_1": stuid0,
            "player_2": stuid1,
            "winner": winner,
            "mystery": mystery
        })
        # if hasattr(histid, 'isnumeric'):
        #     if histid.isnumeric() is False:
        #         raise ValueError("History id is not an integer")
        # sthist = str(histid) if isinstance(histid, int) else histid
        # self._db.execute("insert into history values (?, ?, ?, ?, ?)",
        #                  (sthist, stuid0, stuid1, winner, mystery))

    def get_users_uid(self) -> Generator[str, None, None]:
        # const = "select uid from users"
        # cur = self._db.execute(const)
        # data = cur.fetchall()
        # if GameConfig.SQLConfig.ExpensiveTask is False:
        #     return [UUID(a[0]) for a in data]
        # return [self.get_user(a[0]) for a in data]
        return (user.uid for user in self._users.select())
