"""Linux utilitation"""

from platform import system
from subprocess import Popen, DEVNULL, PIPE
from typing import Union, List, AnyStr
from shlex import split

if system() != "Linux":
    raise OSError("This OS is not Linux.")


def _pa_helpers(x): return x.replace('_', '-').replace('__', '_')


def parse_args(*args, **kwargs):
    d = []
    d.extend(args)
    for k, v in tuple(kwargs.items()):
        if v is None or v is False:
            # Pass on None, ex. linuxfunction(hack=None) --> linuxfunction
            # linuxfunction(hack=True) --> linuxfunction --hack
            continue

        if len(k) == 1:
            d.extend(('-'+k) if v is not True else ('-'+k, str(v)))
            continue
        d.extend(('--'+_pa_helpers(k))
                 if v is not True else ('--'+_pa_helpers(k), str(v)))
    return d


def popen(popen_args: Union[List[str], AnyStr], **popen_kwargs) -> str:
    """For help, seek at subprocess.Popen but the default of everything is:
    stdin  -> DEVNULL
    stdout -> PIPE
    stderr -> None
    text   -> True"""

    def oppose(key, value): return None if value not in popen_kwargs else popen_kwargs.__setitem__(
        key, value)
    force_oppose = popen_kwargs.__setitem__
    oppose('stdin', DEVNULL)
    oppose('stdout', PIPE)
    oppose("text", True)
    popen_args = popen_args if not isinstance(
        popen_args, str) else split(popen_args)
    proc = Popen(popen_args, **popen_kwargs)
    force_oppose('shell', False)
    return proc.communicate()[0]
