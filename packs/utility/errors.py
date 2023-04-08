"""Errors"""

from warnings import warn


class AssignedProtocolError(Exception):
    """A prefix protocol is already defined"""


class NewUserWarning(UserWarning):
    def warn(self, message: str, *args, **kwargs):
        warn(message, self.__class__, *args, **kwargs)


class RedefineIsRequired(NewUserWarning):
    """This method needs to re-defined on subclass."""

    def warn(self, *args, **kwargs):
        super().warn("This method needs to re-defined on subclass", *args, **kwargs)
