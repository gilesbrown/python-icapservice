from __future__ import print_function, unicode_literals
from datetime import datetime
from itertools import chain
from six import iteritems, binary_type, next
from six.moves.http_client import responses


RFC1123_DATETIME_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'
STATUS_LINE = b'{} {} {}\r\n'
CRLF = b'\r\n'


reasons = dict(responses)
reasons.update({
    100: 'Continue after ICAP Preview',
    204: 'No modifications needed',
    404: 'ICAP Service not found',
    405: 'Method not allowed for service',
    408: 'Request timeout',
    500: 'Server error',
})


class ICAPResponseHeaders(dict):

    def __setitem__(self, key, value):
        return super(ICAPResponseHeaders, self).__setitem__(key.title(), value)

    def write(self, wfile):
        for key, value in iteritems(self):
            if isinstance(value, list):
                line = '{}: {}\r\n'.format(key, ', '.join(value))
            else:
                line = '{}: {}\r\n'.format(key, value)
            wfile.write(line)
        wfile.write(CRLF)


def now_rfc1123():
    return datetime.utcnow().strftime(RFC1123_DATETIME_FORMAT)


class ICAPResponse(object):

    protocol = 'ICAP/1.0'

    def __init__(self, status_code=200, **kw):
        self.status_code = status_code
        self.reason = kw.pop('reason', reasons[self.status_code])
        self.headers = ICAPResponseHeaders()
        self.headers.update(kw.pop('headers', {}))
        self.headers.setdefault('Date', now_rfc1123())
        self.encapsulated_request = kw.pop('encapsulated_request', None)
        self.encapsulated_response = kw.pop('encapsulated_response', None)
        self.has_empty_body = False
        if kw:
            raise ValueError('unexpected keyword arguments %r' % kw)
        if self.encapsulated_response and self.encapsulated_request:
            raise ValueError('cannot encapsulate both request and response')
        self.wfile = None

    def write(self, wfile, body_chunks):

        self.wfile = wfile

        other_chunks  = iter(body_chunks)
        try:
            first_chunk = [next(other_chunks)]
        except StopIteration:
            first_chunk = []

        status_line = STATUS_LINE.format(self.protocol,
                                         self.status_code,
                                         self.reason)
        wfile.write(status_line)

        assert self.status_code not in (100, 204)

        self.write_encapsulated(wfile, first_chunk)

        for chunk in chain(first_chunk, other_chunks):
            formatted = b'{:x}\r\n{}\r\n'.format(len(chunk), chunk)
            wfile.write(formatted)

        if first_chunk:
            self.wfile.write(b'0\r\n\r\n')

        self.wfile.flush()

    @classmethod
    def write_100(cls, wfile):
        wfile.write(b'{} 100 {}\r\n\r\n'.format(cls.protocol, reasons[100]))
        # generally we flush at the end of the response, but here we need
        # the intermediate response to be seen right now
        wfile.flush()

    @classmethod
    def write_204(cls, wfile):
        wfile.write(b'{} 204 {}\r\n\r\n'.format(cls.protocol, reasons[204]))

    def write_encapsulated(self, wfile, first_chunk):

        header = []
        msg = b''
        body_type = None

        if self.encapsulated_response:
            msg = binary_type(self.encapsulated_response)
            header.append('res-hdr=0')
            body_type = 'res-body'
        elif self.encapsulated_request:
            msg = binary_type(self.encapsulated_request)
            header.append('req-hdr=0')
            body_type = 'req-body'

        body_type = 'null-body' if not first_chunk else body_type
        header.append('{}={}'.format(body_type, len(msg)))

        self.headers['Encapsulated'] = header
        self.headers.write(wfile)
        wfile.write(msg)
