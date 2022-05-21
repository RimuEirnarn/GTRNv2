from sqlite3 import Connection
from typing import Iterable
from libutil import Symbol
from string import punctuation, whitespace


def _checkname(data):
    p = punctuation.replace('_', '')+whitespace
    for i in data:
        if i in p:
            return False
    return True


class DataTypes(Symbol):
    _sqltypes = {}

    def __new__(cls, name, nocall=False):
        if name in cls._sym:
            return cls._sym[name]
        self = object.__new__(cls)
        DataTypes._sqltypes[name] = self
        return self

    def __init__(self, name: str, nocall=False):
        self._name: str = name
        self._value = self._name
        self._nval: int = None
        self._nocall = nocall

    def __str__(self):
        return self._value

    def __call__(self, value: int):
        return f"{self._value}({value})" if self._nocall else self._value

    def __repr__(self):
        return f"DataType(%s)" % self._name


class Check:
    def __init__(self, name):
        self._name = name

    def __eq__(self, other):
        return f"check ({self._name}=={other.__str__()})"

    def __ne__(self, other):
        return f"check ({self._name}!={other.__str__()}"

    def __ge__(self, other):
        return f"check ({self._name}>={other.__str__()}"

    def __gt__(self, other):
        return f"check ({self._name}>{other.__str__()}"

    def __le__(self, other):
        return f"check ({self._name}<={other.__str__()})"

    def __lt__(self, other):
        return f"check ({self._name}<{other.__str__()})"

    def __repr__(self):
        return f"Check(%s)" % self._name


class TableExistsError(Exception):
    """Table exists"""

    def __init__(self, name):
        self._arg = f"Name {name} is exists"
        super().__init__(self._arg)


class SecurityException(Exception):
    """Certain action blocked by security reason."""


autoincrement = Symbol("AutoIncrement", 'autoincrement')
primary_key = Symbol("Primary Key", 'primary key')
foreign_key = Symbol("Foreign Key", 'foreign key')
not_null = Symbol("NotNull", 'not null')
unique = Symbol("Unique", "unique")

integer = DataTypes("integer")
string = DataTypes('text')


class Value:
    def __init__(self, name, typename: DataTypes, *args):
        if _checkname(name) is False:
            raise Exception("The name has some unallowed characters")
        self._name = name
        self._type = typename
        self._args = [a._value for a in args]

    def __str__(self):
        return f"{self._name} {self._type}{' ' if len(self._args) != 0 else ''}{' '.join(self._args)}"

    def __repr__(self):
        return self.__str__()


def _checktable(db: Connection, table_name: str):
    cur = db.execute("select name from sqlite_master where type='table' and name=:name", {
                     "name": table_name})
    if cur.fetchone() is None:
        return False
    return True


def _common_table_check(db: Connection, table_name: str, exists_ok=False):
    if _checkname(table_name) is False:
        raise SecurityException("The name has some unallowed characters")
    if _checktable(db, table_name) is True and exists_ok is False:
        raise TableExistsError(table_name)


def make_table(db: Connection, table_name, *values: Iterable[Value]):
    _common_table_check(db, table_name)
    cur = db.cursor()
    nconst = ""
    for v in values:
        nconst += ', '+v.__str__()
    nconst = nconst[2:][:-1]
    const = f"""create table {table_name} ({nconst})"""
    cur.execute(const)
    db.commit()


def alter_table(db: Connection, table_name: str, command: str, colname, **kwargs):
    _common_table_check(db, table_name)
    if command == 'add':
        db.execute(
            f"alter table {table_name} add {_checkname(colname)} {kwargs['datatype']}")
    if command == 'drop':
        db.execute(
            f"alter table {table_name} drop column {_checkname(colname)}")


def drop_table(db: Connection, table_name: str):
    _common_table_check(db, table_name, exists_ok=True)
    db.execute(f"drop table {table_name}")


def truncate_table(db: Connection, table_name: str):
    _common_table_check(db, table_name, exists_ok=True)
    db.execute(f"truncate table {table_name}")
