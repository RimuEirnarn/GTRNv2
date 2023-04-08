"""Installation helpers on global (Linux's /usr)

Helper module for installing on /usr. This module is unused for MacOS and Windows."""

from platform import system

if system() != 'Linux':
    raise OSError(
        f"{system()} is not Linux. It requires setuid and setgid to install.")

from packs.liblinuxutil import parse_args, popen


def adduser(username, group=None, **configs):
    x = ['adduser']
    x.extend(parse_args(username, group, **configs))
    popen(x)
