from enum import Enum
import socket
from socket import SOCK_STREAM, AF_INET, AF_UNIX, SocketType
from base64 import b64encode, b64decode
from typing import Literal, NamedTuple, Union
from urllib.request import urlopen
from urllib.parse import urlsplit, parse_qs
from json import dumps as parse_json, loads as load_json
import warnings
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

def _parse_message(**kwargs) -> str:
    """It's better to encode it first. Also, it's word-based."""
    d = ""
    compress = lambda x: ':'.join(x)
    for a,b in kwargs.items():
        a, b = str(a), str(b) if not isinstance(b, (list, set, tuple)) else compress(b)
        if ' ' in a or ' ' in b:
            warnings.warn(f"Space in word-only identifier. {a!r} | {b!r}")
            continue
        d+=f"{a}[{b}] "
    return d[:-1]


def _load_message(data: str) -> dict[str, Union[tuple[str], str]]:
    splitted: list[str] = data.split(" ")
    true_data: dict[str, str] = {}
    for a in splitted:
        if (from_ :=a.find('[')) == -1:
            continue
        if (to := a.find(']')) == -1:
            continue
        content = a[from_+1:to]
        content: Union[tuple[str], str] = tuple(content.split(":"))
        if len(content) == 1:
            content: Union[tuple[str], str] = content[0]
        true_data[a[:from_]] = content
    return true_data

class StatusContent(NamedTuple):
    code: int
    description: str

    def __int__(self):
        return self.code
    
    def __str__(self):
        return self.description
    
    def __repr__(self):
        return f"{type(self).__name__}[{self.code}]"
    
    def __eq__(self, other: int):
        if not isinstance(other, int):
            raise TypeError("Expected int, got {0}.".format(type(other)))
        return self.code == other

class StatusENUM(Enum):
    # Passing on!
    NULL = StatusContent(0, '')
    GOOD = StatusContent(1, "The request is accepted.")
    WAITING = StatusContent(2, "You can send more, i'm waiting.")
    DONE = StatusContent(3, "The request is accepted and the content is created.")
    DELETED = StatusContent(4, "The request is accepted and the content is erased.")
    EXISTS = StatusContent(5, "The request is accepted and the content exists.")
    CONNECT_SUCCESS = StatusContent(6, "Your connection is established and you are logged in.")
    CONNECT_LOGOUT = StatusContent(7, "Bye-bye!")

    # Error/Client
    BLOCKED = StatusContent(100, "There's error in matrix, please be more careful with auth.")
    CONNECT_FAILED = StatusContent(101, "Your connection is failed, try again but don't be mad.")
    NOT_EXISTS = StatusContent(102, "Uh, the thing you are refering is not even exists. Try again.")
    ALREADY_EXISTS = StatusContent(103, "Uh, the thing you are refering is already exists. Try again.")
    REQ_SYNTAX_ERROR = StatusContent(104, "Your request have some syntax errors. Try again with better one.")
    USER_NOT_FOUND = StatusContent(105, "The user you want to login as is not found. Try to use sign-in method.")

    ## Error/Client + Internals
    PERMISSION_DENIED = StatusContent(110, "You are not allowed to do something with what you're refering to.")

    # Error/Server
    INTERNAL_SERVER_ERROR = StatusContent(200, "Internal Server Error")
    MAINTENANCE = StatusContent(201, "We are still in maintenance. Please try again later.")
    OVERFLOW = StatusContent(202, "Total Request that we got is too much!")

    # Client's status

    REQUEST_NORETURN = StatusContent(300, "Please process this request")
    REQUEST_GET = StatusContent(301, "Can i get info with this request?")
    REQUEST_POST = StatusContent(302, "Can you put this?")
    REQUEST_DELETE = StatusContent(303, "Can i delete this?")
    REQUEST_SUBSCRIBE = StatusContent(304, "Put me in broadcast mode, please")
    REQUEST_DONE = StatusContent(305, "I want to quit the broadcast mode.")

    @staticmethod
    def get(value: int) -> StatusContent:
        for status in StatusENUM:
            if status.value.code == value:
                return status.value
        return StatusENUM.NULL

    @staticmethod
    def getstr(value: int) -> str:
        return StatusENUM.get(value).description
        

class Response:
    def __init__(self, status: int, summary: Union[str, bytes], body: Union[str, bytes], *, raw: Union[str, bytes]=None):
        self._status = StatusENUM.get(status)
        if self._status.description == '':
            raise Exception("Request made probably with future version. Unknown status: %s" % status)
        self._body = body if isinstance(body, str) else body.decode()
        self._sum = summary if isinstance(summary, str) else summary.decode()
        self._raw = f"{status} - {summary}\n\0{body}" if raw is None else (raw if isinstance(raw, str) else raw.decode())

    def __repr__(self):
        return f"<Response: {self.status} Length={len(self.body)}>"
    
    @property
    def status(self):
        """Status code of the response"""
        return self._status
    
    @property
    def body(self):
        """Response content"""
        return self._bodystatus
    
    @property
    def message(self):
        """1-line message"""
        return self._sum


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
        self._flag = -1
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
    
    @property
    def sockAs(self):
        return "Client" if self._flag == 1 else ("Server" if self._flag == 2 else ("Unitialized" if self._flag == -1 else "Undefined"))

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
        self._flag = 2

    def close(self):
        self._socket.close()

    def read_base(self, bufflen: int=None):
        encoding = self._query.get("encoding", 'utf-8')
        errors = self._query.get('errors', '')
        data = ""
        if bufflen is not None:
            return self._socket.recv(1024).decode(encoding, errors)
        while True:
            b = self._socket.recv(1024).decode(encoding, errors)
            if b == '':
                break
            data += b
        return data

    def read(self, bufflen: int=None) -> Response:
        body = self.read_base(bufflen)
        # Expected:
        #   CODE - 1-line response\n\0BODY
        firstline,data = body.split("\n\0")
        code, summary = firstline.split(' - ')
        summary = ' - '.join(summary)
        if not code.isnumeric():
            code = "0"
        return Response(int(code), summary, data, raw=body)

    def send_base(self, data: Union[bytes, str]):
        encoding = self._query.get("encoding", 'utf-8')
        errors = self._query.get('errors', '')
        return self._socket.send(data.encode(encoding, errors)) if isinstance(data, str) else self._socket.send(data)
    
    def send(self, data: Union[bytes, str], *, code: int=None, summary: Union[bytes, str]=None):
        pad = '\n\0'
        if summary is None and '\n' not in data:
            summary, data = data, summary
        body = f"{code} - {summary}{pad+data if data else ''}"
        self.send_base(body)
    
    def communicate(self, data: Union[bytes, str], *, code: int=None, summary: Union[bytes, str]=None) -> Response:
        self.send(data, code=code, summary=summary)
        return self.read()

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
        self._flag = 1

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
#  Push room as Owner[SessionKey]
#  <header>
#    IncludePlayerSharedID: <Username>, ...
#    LevelRoom: 1
#    IncludeBots: True
#  </header>
# Joining a room:
#  Push self[Username:SessionKey] to Room[RID]
# Delete a room:
#  Delete Room[RID] as Owner[Username:SessionKey]
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


class BaseClient:
    def __init__(self, server):
        self._server = BaseSocketProtocol(server)
        self._username = None
        self._encoded_name = None
        self._session_key = None
        self._esk = None
        self._client_identifier = {}

    def get(self):
        pass

    def put(self):
        pass

    def do_connect(self, username: str, password: str):
        """Connnect to server"""
        self._server.connect()
        eu, ep = b64encode(username, '-_'), b64encode(password, '-_')
        self._encoded_name = eu
        resp = self._server.communicate(f"Connect with AN[{eu}] and AP[{ep}]")
        if resp.status == 105:
            resp = self._server.communicate(f"Push Data as AN[{eu}] and AP[{ep}] then Connect", code=302)
            if resp.status == 6:
                self._username = username
                self._client_identifier['login-cred'] = resp.body
                self._client_identifier['login-sum'] = resp.message
                self._session_key = b64decode(_load_message(resp.body)['You'])
                self._esk = _load_message(resp.body)['You']
                return
        raise ConnectionError("Unable to log in, invalid status code: %d (%s)" % (resp.status.code, resp.status.description))

    def do_make_room(self, **contents):
        """Push a request to the server; Making a room.
        
        In contents you may include these:
            Invites: <Username>[, ...]
            Level: <Level> # default -> 2
            Bots: <boolean>"""
        eid = self._session_key
        resp = self._server.communicate(parse_json(contents), code=302, summary=f"Push room as Owner[{eid}]")
        if resp.status != 1:
            raise ConnectionError(f"[Errno {resp.status.code}] {resp.status.description} | {resp.message}")
        self._client_identifier['room'] = load_json(resp.body)
    
    def do_join_room(self, room_id: int):
        """Join a room made by somebody. PS, you can't call this if room key is exists/not none"""
        if self._client_identifier.get("room", None) is not None:
            raise Exception("Cannot join while already joined/created a room.")
        # The server will still mad if we're 'forcing' to join another room without calling disconnect
        eid = self._session_key
        resp = self._server.communicate(f"Push self[{self._encoded_name}:{eid}] to Room[{room_id}]", code=302)
        if resp.status.code != 1:
            raise ConnectionError(f"[Errno {resp.status.code}] {resp.status.description} | {resp.message}")
        self._client_identifier['room'] = load_json(resp.body)
    
    def do_exit_room(self):
        # We assume JSON on ClientIdentifier:room has these data:
        #   RoomID: <RID>
        #   Owner : <USERNAME#PUID>
        #   RoomLn: <integer>
        if self._client_identifier['room']['RoomLn'] != 0 or self._client_identifier['room']['Owner'] != self._username:
            resp = self._server.communicate(f"Disconnect self[{self._encoded_name}:{self._esk} from Room[{self._client_identifier['room']['RoomID']}]", code=303)
            # if it fails, just ignore and remove the room data.
            del resp, self._client_identifier['room']
            return
        resp = self._server.communicate(f"Remove Room[{self._client_identifier['room']['RoomID']}] as Owner[{self._encoded_name}:{self._esk}]")
        del resp, self._client_identifier['room']
    
    def do_get_info(self, request_type: Literal["account", 'room']) -> dict:
        if not request_type in ("account", 'room'):
            raise Exception("Invalid request. Expected 'account' or 'room', got '%s'" % request_type)
        resp = self._server.communicate(f"Take data of self[{self._encoded_name}:{self._session_key}]" if request_type else (f'Take data of room[{self._client_identifier["room"]["roomID"]}] and self[{self._encoded_name}:{self._esk}]'))
        if resp.status != 1:
            raise ConnectionError(f"[Errno {resp.status.code}] {resp.status.description} | {resp.message}")
        return load_json(resp.body)