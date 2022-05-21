from collections import UserList, namedtuple
from dataclasses import dataclass
from json import loads
from random import randint
from time import sleep
from typing import Dict, Iterable, List, NamedTuple, Protocol
from sqlite3 import connect
from typing import Any, Union
from uuid import UUID

try:
    from .libutil import Configuration, Symbol, make_uid, RedefineIsRequired
    from .libutilsql import make_table, string, integer, Value, primary_key, _checktable, truncate_table, unique
except ImportError:
    from libutil import Configuration, Symbol, make_uid, RedefineIsRequired
    from libutilsql import make_table, string, integer, Value, primary_key, _checktable, truncate_table, unique

GlobalConfig = Configuration("GlobalConfig")
GameConfig = Configuration("GameConfig",
                           {
                               "DataPath": "project:///game.db",
                               "LogPath": "project:///logs/",
                               "CrashLogPath": "project:///crash/",
                               "PluginPath": "project:///plugins/",
                               "DownloadPath": "project:///downloads/",
                               "IsDebug": True})
SQLConfig = Configuration("SQLConfig", {
    "ChangeInner": False,  # Change in dcur.fetchX()
    # only GameDB.get_history_data, making uid0 and uid1 use User (calling .get_user 2 times)
    "ExpensiveTask": False
})
GlobalConfig.GameConfig = GameConfig
GameConfig.SQLConfig = SQLConfig


def _namedtuple_factory(cursor, row):
    d = []
    e = []
    for idx, col in enumerate(cursor.description):
        d.append(col[0])
        e.append(row[idx])
    a = namedtuple("Record", d)
    return a(*e)


class UserStat(NamedTuple):
    victories: int
    defeats: int


class UserHistory(UserList):
    def __repr__(self):
        return f"UserHistory({len(self)})"


class User(NamedTuple):
    uid: Union[str, UUID]
    username: str
    statistic: Union[UserStat, tuple, str]
    str_statistic: str
    histories: Union[UserHistory, list, str]


class History(NamedTuple):
    histid: int
    uid0: Union[str, UUID, User]
    uid1: Union[str, UUID, User]
    winner: int
    mystery: int


class GameDB:
    """Game database"""
    _instance = None

    def __init_subclass__(cls) -> None:
        raise Exception("This class cannot be subclassed.")

    def __new__(cls):
        if cls._instance is not None:
            return cls._instance

        self = super(GameDB, cls).__new__(cls)
        cls._instance = self
        return self

    def __initdb__(self):
        make_table(self._db, 'users', Value('uid', string, primary_key), Value(
            'username', string), Value('statistic', string), Value('history_ids', string))
        make_table(self._db, 'history', Value('id', integer, primary_key), Value(
            'uid0', string), Value('uid1', string), Value('winner', integer), Value('mystery', integer))
        self.add_user('debug')

    def __init__(self):
        if GameConfig.IsDebug is True:
            self._db = connect(":memory:")
            self.__initdb__()
        else:
            self._db = connect(GameConfig.DataPath)
            if _checktable(self._db, "users") is False:
                self.__initdb__()
        if GameConfig.SQLConfig.ChangeInner is True:
            self._db.row_factory = _namedtuple_factory
            GameConfig.SQLConfig.ExpensiveTask = False

    def add_user(self, username: str) -> UUID:
        """Add user"""
        uid = make_uid(username)
        stuid = str(uid)
        self._db.execute(f"insert into users values (?, ?, ?, ?)",
                         (stuid, username, '0$0', '[]'))
        self._db.commit()
        return uid

    def remove_user(self, uid: Union[UUID, str]):
        """Remove user"""
        stuid = uid if isinstance(uid, str) else str(uid)
        self._db.execute('delete from users where uid=:uid', {"uid": stuid})

    def mod_user(self, uid: Union[UUID, str], username: str = None, statistic: str = None, history_list: str = None):
        """Modify user's data"""
        if sum((bool(username), bool(statistic), bool(history_list))) == 0:
            raise Exception("Nothing is edited.")
        stuid = uid if isinstance(uid, str) else str(uid)
        injected = ''
        key = {'uid': stuid}
        if username:
            injected += 'username=:username, '
            key['username'] = username
        if statistic:
            injected += 'statistic=:statistic, '
            key['statistic'] = statistic
        if history_list:
            injected += 'history_ids=:history_ids, '
            key['history_ids'] = history_list
        const = f'update users set {injected[:-2]} where uid=:uid'
        self._db.execute(const, key)

    def remove_history(self):
        """Remove history"""
        truncate_table(self._db, 'history')

    def reset(self):
        """Reset the database"""
        truncate_table(self._db, "users")
        truncate_table(self._db, 'history')
        self.add_user('debug')

    def mod_settings(self, **kwargs):
        """Change game config"""
        GameConfig.__update__(kwargs)

    def get_user(self, uid: Union[str, UUID]) -> Union[None, Any]:
        self._force_no()
        stuid = uid if isinstance(uid, str) else str(uid)
        cur = self._db.execute(
            "select uid, username, statistic, history_ids from users where uid=:uid", {'uid': stuid})
        if GameConfig.SQLConfig.ExpensiveTask is True:
            c = cur.fetchone()
            _a = UUID(c[0])
            _b = c[1]
            _c = c[2].split('$')
            _d = UserStat(_b[0], _b[2])
            _e = UserHistory(loads(c[-1]))
            return User(_a, _b, _c, c[2], _e)
        elif GameConfig.SQLConfig.ChangeInner is False:
            c = cur.fetchone()
            return User(c[0], c[1], UserStat(*c[2].split('$')), c[2], c[3])
        return cur.fetchone()

    def get_history_data(self, histid: Union[int, str]):
        self._force_no()
        if hasattr(histid, 'isnumeric'):
            if histid.isnumeric() is False:
                raise ValueError("History id is not an integer")
        sthist = str(histid) if isinstance(histid, int) else histid
        cur = self._db.execute(
            'select id, uid0, uid1, winner, mystery from history where id=:id', {'id': sthist})
        if GameConfig.SQLConfig.ExpensiveTask is True:
            c = cur.fetchone()
            a, u0, u1, w, m = c
            u0 = self.get_user(u0)
            u1 = self.get_user(u1)
            return History(a, u0, u1, w, m)
        elif GameConfig.SQLConfig.ChangeInner is False:
            return History(*cur.fetchone())
        return cur.fetchone()

    def add_history(self, histid: Union[int, str], uid0: Union[str, UUID], uid1: Union[str, UUID], winner: int, mystery: int):
        self._force_no()
        stuid0 = uid0 if isinstance(uid0, str) else str(uid0)
        stuid1 = uid1 if isinstance(uid1, str) else str(uid1)
        if hasattr(histid, 'isnumeric'):
            if histid.isnumeric() is False:
                raise ValueError("History id is not an integer")
        sthist = str(histid) if isinstance(histid, int) else histid
        self._db.execute("insert into history values (?, ?, ?, ?, ?)",
                         (sthist, stuid0, stuid1, winner, mystery))

    def _force_no(self):
        if self._db.row_factory is _namedtuple_factory:
            GameConfig.SQLConfig.ExpensiveTask = False
            GameConfig.SQLConfig.ChangeInner = True

    def get_users_uid(self) -> tuple:
        const = "select uid from users"
        cur = self._db.execute(const)
        data = cur.fetchall()
        if GameConfig.SQLConfig.ExpensiveTask is False:
            return [UUID(a[0]) for a in data]
        return [self.get_user(a[0]) for a in data]


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
    level: Dict[int, List[int]] = {i: [2**v, -2**v]
                                   for i, v in enumerate(range(5, 106))}

    def __new__(cls, *args, **kwargs):
        if cls in BaseGame._instance:
            return BaseGame._instance[cls]
        self = super().__new__(cls)
        cls._instance[cls] = self
        return self

    def __init__(self):
        self._players: List[ProtoPlayer] = []
        self._mystery = None
        self._running = False
        self._database = GameDB()
        self._level = 0
        self._turn = 0
        self._winner = []
        self._request_state = already_stop

    def register_player(self, player: Any):
        if self._running is True:
            return
        self._players.append(player)

    def scan_value(self, player: 'ProtoPlayer', value: int):
        if self._mystery is None:
            raise Exception("Mystery number is missing")
        if value == self._mystery:
            self._winner.append(player)
            self._request_state = stop_game
        return Identifier(player, big if value > self._mystery else (None if self._mystery == value else small), value)

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
        self._request_state = already_stop
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
        return f"<{type(self).__name__} State={self._request_state._name} Players={len(self._players)} Running={self._running}>"


class ZeroPlayer(BaseGame):
    def __init__(self, bots: int = 0, level: int = 5):
        super().__init__()
        self.set_level(level)
        self._players.append(Bot("Bot-0", self._level))
        if bots > 1:
            for a in range(1, bots):
                self._players.append(Bot(f"Bot-{a}", self._level))

    def run(self):
        smin = BaseGame.level.get(self._level, [None, -1024])[1]
        smax = BaseGame.level.get(self._level, [1024, None])[0]
        self._mystery = randint(smin, smax)
        self._running = True
        self._turn = 0
        flag = None
        for p in self._players:
            if hasattr(p, 'tell'):
                p.tell(maxplayers=len(self._players))
        print(
            f"Mystery Number: {self._mystery} (level {self._level})\nRanging from: {smin} to {smax}")
        while self._running is True:
            self._turn += 1
            print(f"Turn {self._turn}")
            for p in self._players:
                try:
                    player_input = p.get()
                    identifier = self.scan_value(p, player_input)
                    print(
                        f"{p.Name}: {player_input} {'(Too big)' if identifier.was is big else ('(Too small)' if identifier.was is small else 'Correct!')}")
                    [_p.push_put(identifier)
                     for _p in self._players if hasattr(_p, 'push_put')]
                except KeyboardInterrupt:
                    try:
                        input("Interrupted.")
                    except KeyboardInterrupt:
                        self._running = False
                        break
            if self._request_state == stop_game:
                self._running = False
        print(
            f'Game ends in {self._turn} turn(s) with {len(self._winner)} winning player(s)!')


class ProtoPlayer(Protocol):
    def get_id(self) -> Union[str, UUID, None]:
        pass

    def get(self) -> int:
        pass

    def put(self, minvalue: int, maxvalue: int):
        pass

    def reset(self):
        pass

    @property
    def Name(self) -> str:
        return 'ProtoPlayer[Name]'


class BasePlayer:
    def __init__(self, name: str, level: int):
        self._uid: UUID = None
        self._name = name
        self._level = level

    def get(self):
        return None

    def put(self, minvalue: int, maxvalue: int):
        pass

    def __repr__(self):
        return f"{type(self).__name__}({self._name})"

    def get_id(self):
        return self._name if not hasattr(self, '_uid') else self._uid

    def reset(self):
        pass

    @property
    def Name(self):
        return self._name


class Bot(BasePlayer):
    def __init__(self, name: str, level: int):
        super().__init__(name, level)
        self._max = BaseGame.level.get(level, [1024, None])[0]
        self._min = BaseGame.level.get(level, [None, -1024])[1]
        self._last = []
        self._pendings = []
        self._max_pending = 1

    def put(self, minvalue: int, maxvalue: int):
        if minvalue is not None and isinstance(minvalue, int):
            self._min = minvalue+1 if self._min < minvalue else self._min
        if maxvalue is not None and isinstance(maxvalue, int):
            self._max = maxvalue-1 if self._max > maxvalue else self._max

    def put_max(self, maxvalue: int):
        self.put(None, maxvalue)

    def put_min(self, minvalue: int):
        self.put(minvalue, None)

    def get(self):
        if self._max == self._min:
            return self._max

        if self._min > self._max:
            self._max, self._min = self._min, self._max
        returner = randint(self._min, self._max)
        while returner in self._last:
            returner = randint(self._min, self._max)
        self._last.append(returner)
        return returner

    def critical_put(self, *values: Iterable['Identifier']):
        if len(values) == 1:
            if isinstance(values[0], (tuple, list)):
                values = values[0]
        mins = [val for val in values if val.was == small]
        maxs = [val for val in values if val.was == big]
        #print(maxs, mins, self, f"{self._min = }", f"{self._max = }")
        _min = max(mins).value if len(mins) != 0 else None
        _max = min(maxs).value if len(maxs) != 0 else None
        #print(self, "min="+str(_min or self._min), "max="+str(_max or self._max), self._level)
        self.put(_min, _max)

    def tell(self, *args, maxplayers=1):
        self._max_pending = maxplayers if maxplayers > 0 else 1

    def push_put(self, value: 'Identifier'):
        #print('On push put!')
        self._pendings.append(value)
        #print(f"Size push: {len(self._pendings)}")
        if self._max_pending == len(self._pendings):
            #print("Reached max pending!")
            self.do_pending()

    def do_pending(self):
        self.critical_put(self._pendings)
        self._pendings.clear()

    def reset(self):
        self._min: int = BaseGame.level.get(self._level, -1024)[1]
        self._max: int = BaseGame.level.get(self._level, 1024)[0]


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
        return f"Identifier({self.player._name})"


def _always_false(x): return False
def _always_true(x): return True


big = Symbol('big', 'bigger', lt_hook=_always_false,
             le_hook=_always_false, gt_hook=_always_true, ge_hook=_always_false)
small = Symbol('small', 'smaller', lt_hook=_always_true,
               le_hook=_always_true, gt_hook=_always_false, ge_hook=_always_false)
keep_running = Symbol('KeepRunning', 'Keep')
stop_game = Symbol('StopGame', 'Stopping')
already_stop = Symbol('AlreadyStop', 'Stop')
