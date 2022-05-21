import socket
from socket import SOCK_STREAM, AF_INET, AF_UNIX, SocketType
from base64 import b64encode, b64decode
from typing import Union
from urllib.request import urlopen
from urllib.parse import urlsplit, parse_qs
from libutil import Protocol
from os import remove
from shlex import split as sh_split


def _create_bind_socket(where: Union[tuple, str]):
    if not isinstance(where, (tuple, str)):
        raise TypeError("where must be a tuple or string")

    sock = socket.socket(AF_INET if not isinstance(
        where, str) else AF_UNIX, SOCK_STREAM)
    sock.bind(where)
    sock.listen()
    return sock


def _create_listen_socket(where: Union[tuple, str]):
    if not isinstance(where, (tuple, str)):
        raise TypeError("where must be a tuple or a string")

    sock = socket.socket(AF_INET if not isinstance(
        where, str) else AF_UNIX, SOCK_STREAM)
    sock.connect(where)
    return sock


class HTTPProtocol(Protocol, prefix='http'):
    def __init__(self, url: str):
        super().__init__(url)

    def __call__(self, *args, **kwargs):
        """args and kwargs will be passed to urllib.request.urlopen"""
        return urlopen(self._url, *args, **kwargs)


class BaseSocketProtocol(Protocol, prefix='socket'):
    """Base Socket Protocol

    Use ? at the end of filename as a keyword argument to building the socket"""

    def __init__(self, url: str):
        super().__init__(url)
        self._query = {k: v[0] for k, v in parse_qs(
            urlsplit(self._url).query).items()}
        if self._splitted.netloc == '':
            self._socket = socket.socket(AF_UNIX, SOCK_STREAM)
        else:
            self._socket = socket.socket(AF_INET, SOCK_STREAM)
        self._netloc = self._splitted.netloc.split(':')
        if self._netloc != ['']:
            port = int(self._netloc.pop())
            self._netloc.append(port)
            self._netloc = tuple(self._netloc)
        self._path = self._path[:self._path.find('?')]
        if (sockref := self._query.get("type", None)) is not None:
            if sockref == 'server' or sockref == 's':
                self.bind()
            elif sockref == 'client' or sockref == 'c':
                self.connect()
            else:
                raise ValueError(
                    "Invalid socket type binding (expected s/c/server/client, got %s)" % sockref)

    @property
    def sockType(self):
        return 'UNIX' if self._netloc == [''] else 'INET'

    @property
    def netLocation(self):
        return self._netloc

    @property
    def sockPath(self):
        return self._path if self.sockType == 'UNIX' else ''

    @property
    def sock(self):
        return self._socket

    def bind(self):
        if self.sockType == 'UNIX':
            try:
                self._socket.bind(self._path)
            except OSError as exc:
                if str(exc) == '[Errno 98] Address already in use':
                    remove(self._path)
                    self.bind()
        else:
            self._socket.bind(tuple(self._netloc))
        self._socket.listen()

    def close(self):
        self._socket.close()

    def read(self, bufflen: int):
        encoding = self._query.get("encoding", 'utf-8')
        errors = self._query.get('errors', '')
        return self._socket.recv(bufflen).decode(encoding, errors)

    def send(self, data: Union[bytes, str]):
        encoding = self._query.get("encoding", 'utf-8')
        errors = self._query.get('errors', '')
        return self._socket.send(data.encode(encoding, errors)) if isinstance(data, str) else self._socket.send(data)

    def setblocking(self, value):
        return self._socket.setblocking(value)

    def destroy(self):
        try:
            self.sock.close()
            try:
                self.sock.shutdown(0)
            except OSError:
                pass
            remove(self._path) if self.sockType == 'UNIX' else None
        except Exception:
            pass
        try:
            remove(self._path) if self.sockType == 'UNIX' else None
        except Exception:
            pass

    def accept(self):
        return self.sock.accept()

    def connect(self):
        self.sock.connect(self._path if self.sockType ==
                          'UNIX' else self._netloc)

# XXX: Libnetutil should define how players/device connect with eachother.
# Thus, defining a server would require libserver
# While player/bot base will be defined here.
# But, player/bot class' parent class would not be inheritted from BasePlayer as it's
# not possible because of circular import.
# But we can use multiple inheritance.

# XXX: Network interaction should be defined in creative/good way.
# It's necessary because we don't want to lose our ideas.

# XXX: Below here is commands for network interaction

# Connecting to server:
#   Connect with AN[Username] and AP[Password]
# Sign-in to server:
#   Push Data with AN[Username] and AP[Password] then Connect
# Delete account:
#   Delete Data as AN[Username:SessionKey] where data is Account
# Creating room:
#  Push room as Owner[Username] with AI[SessionKey]
#  <header>
#    IncludePlayerSharedID: <UUID>, ...
#    LevelRoom: 1
#    IncludeBots: True
#  </header>
# Joining a room:
#  Push self[Username:SessionKey] to Room[RID]
# Delete a room:
#  Delete room as Owner[Username:SessionKey]
#  <or>
#  Disconnect self[Username:SessionKey] from Room[RID]
# Retrieve user information
#  Take data of self[Username:SessionKey]
# Retrieve room information
#  Take data of Room[RID] and self[Username:SessionKey]

# Server responses:
# 1. Connected You[SessionKey]
# 2. Connected You[SessionKey] and message is "Welcome to {server name}!"
# 3. Deleted You[Username] and message is "Thank you for playing!"
# 4. Created Room[RID] with Owner[UserID]
# 5. Pushed You to Room[RID]
# 6. Removed You from Room[RID]
# 7. Send Data of You to AI[UserID]
#    <header>
#      ...
#    </header>
# 8. Send Data of Room[RID] to You[UserID]
#    <header>
#      ...
#    </header>


class BaseNetwork:
    def __init__(self, server):
        self._server = Protocol(server)

    def get(self):
        pass

    def put(self):
        pass
