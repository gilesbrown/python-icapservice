from __future__ import print_function, unicode_literals
from copy import deepcopy
from six.moves.http_client import HTTPMessage
from six import PY2
from .response import OK


START_LINE = b'{} {} {}\r\n'
CRLF = b'\r\n'


def split_start_line(start_line):
    """ Split the start line (see RFC2616 section 4). """
    return start_line.rstrip().split(None, 2)


class HTTPRequest(HTTPMessage):

    @classmethod
    def parse(cls, rfile):
        method, uri, protocol = split_start_line(rfile.readline())
        message = cls(rfile)
        message.method = method
        message.uri = uri
        message.protocol = protocol
        return message

    def modify(self):
        return OK(http_request=deepcopy(self))

    def __bytes__(self):
        start_line = START_LINE.format(self.method,
                                       self.uri,
                                       self.protocol)
        return start_line + b''.join(self.headers) + CRLF

    if PY2:
        __str__ = __bytes__


class HTTPResponse(HTTPMessage):

    @classmethod
    def parse(cls, rfile):
        protocol, status_code, reason = split_start_line(rfile.readline())
        message = cls(rfile)
        message.protocol = protocol
        message.status_code = int(status_code)
        message.reason = reason
        return message

    def __bytes__(self):
        start_line = START_LINE.format(self.protocol,
                                       self.status_code,
                                       self.reason)
        return start_line + b''.join(self.headers) + CRLF

    if PY2:
        __str__ = __bytes__
