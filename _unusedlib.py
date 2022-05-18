"""Archived core library"""

from warnings import warn

warn("This module is deprecated and will be removed in future.")

if False is True:

    from sqlalchemy import create_engine, Column, String, Integer
    from sqlalchemy.engine.base import Connection as _con
    from sqlalchemy.engine.mock import MockConnection as _moc
    from sqlalchemy.orm import declarative_base, sessionmaker
    from typing import Union
    try:
        from .libutil import Memory, Configuration, Symbol, _check_prefix, make_uid
    except ImportError:
        from libutil import Memory, Configuration, Symbol, _check_prefix, make_uid

    _const_symconf = Symbol('FlagConfig', 'GlobalConfig')
    _const_engine = None
    _const_db = None
    _const_base = declarative_base()
    _const_config = Configuration(_const_symconf)
    _const_config.game = \
        Configuration("GameConfig",
                      {
                          "DataPath": "project:///game.db",
                          "LogPath": "project:///logs/",
                          "CrashLogPath": "project:///crash/",
                          "PluginPath": "project:///plugins/",
                          "DownloadPath": "project:///downloads/",
                      })


    def init_db(path: str = Memory, isglobal=True, **kwargs) -> tuple[Union[_moc, _con]]:
        """Init Database

        :param path: Path/url to the database
        :param isglobal: Use the global constant
        :param **kwargs: Additional keyword arguments that will be passed to sqlalchemy.create_engine"""
        global _const_db, _const_engine
        if isglobal is True and _const_engine is not None:
                return _const_db
        i = _check_prefix(path.__str__())
        if i is False:
            if path[0] == '/':  # Replacing ://///etc/passwd into :////etc/passwd
                path = path[1:]
            path = 'sqlite+pysqlite:////' + path
        engine = create_engine(path, **kwargs)
        db: _con = engine.connect()
        session = sessionmaker(engine)
        if isglobal is True:
            _const_db = db
            _const_engine = engine
        return engine, db


    class _User(_const_base):
        __tablename__ = 'users'
        uid = Column(String, primary_key=True)
        name = Column(String)
        statistic = Column(String)
        history_ids = Column(String) # JSON

        def __repr__(self):
            return "User(%s - %s)" % (self.name, self.uid)

    class _History(_const_base):
        __tablename__ = "history"
        history_id = Column(Integer, primary_key=True, autoincrement=True)
        uid0 = Column(String)
        uid1 = Column(String)
        winner = Column(String)
        mystery = Column(Integer)

        def __repr__(self):
            return f"History({self.history_id})"


    class GameDB:
        """Game Database class"""

        """
        Table:
          - users
            - uid
            - name
            - statistic
            - history id list (json)
          - history
            - history id
            - uid0
            - uid1
            ...
            - winner
            - mystery
        """

        _instance = None

        def __new__(cls):
            if cls._instance is not None:
                return cls._instance

            self = super().__new__(cls)
            cls._instance = self
            return self

        def __init__(self):
            self._config = _const_db.game
            self._engine, self._db = init_db(self._config.DataPath)
            self._db: _con = self._db

        def add_user(self, name):
            uid = make_uid(name)


__version__ = '0.0.0 [01]'
__author__ = 'RimuEirnarn'
__license__ = 'BSD 3-Clause License'