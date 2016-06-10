from __future__ import print_function, unicode_literals
from datetime import datetime
from io import TextIOWrapper, BytesIO
from functools import partial
from six import iteritems, binary_type, text_type
from six.moves.http_client import responses


RFC1123_DATETIME_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'
STATUS_LINE = b'{} {} {}\r\n'
CRLF = b'\r\n'


icap_reasons = dict(responses)
icap_reasons.update({
    100: 'Continue after ICAP Preview',
    204: 'No modifications needed',
    404: 'ICAP Service not found',
    405: 'Method not allowed for service',
    408: 'Request timeout',
    418: 'Bad composition',
    500: 'Server error',
})

_header_case = {
    'istag': 'ISTag'
}


def header_case(h):
    return _header_case.get(h.lower(), h.title())


class ICAPResponseHeaders(dict):


    def __setitem__(self, key, value):
        return super(ICAPResponseHeaders, self).__setitem__(header_case(key), value)

    def get(self, key):
        return super(ICAPResponseHeaders, self).get(header_case(key))

    def merge(self, other):
        for k, v in iteritems(other):
            self.setdefault(header_case(k), v)


def now_rfc1123():
    return datetime.utcnow().strftime(RFC1123_DATETIME_FORMAT)


class ICAPResponse(object):

    def __init__(self, status_code=200, **kw):
        self.protocol = kw.pop('protocol', 'ICAP/1.0')
        self.status_code = status_code
        self._reason = kw.pop('reason', None)
        self.headers = ICAPResponseHeaders()
        self.headers.update(kw.pop('headers', {}))
        self.headers.setdefault('Date', kw.pop('date', now_rfc1123()))
        self.http_request = kw.pop('http_request', None)
        self.http_response = kw.pop('http_response', None)
        self.has_empty_body = False
        self.chunks = kw.pop('chunks', ())
        if kw:
            raise ValueError('unexpected keyword arguments %r' % kw)
        if self.http_request and self.http_response:
            raise ValueError('cannot encapsulate both request and response')

    def header_bytes(self, any_chunks):

        enc_hdr, enc_msg = self.encapsulated(any_chunks)
        self.headers['Encapsulated'] = enc_hdr

        bio = BytesIO()
        sio = TextIOWrapper(bio, encoding='iso-8859-1')

        status_line = '{} {} {}\r\n'.format(self.protocol,
                                            self.status_code,
                                            self.reason)
        sio.write(status_line)
        for key, value in iteritems(self.headers):
            if isinstance(value, list):
                values = [text_type(v) for v in value]
                line = '{}: {}\r\n'.format(key, ', '.join(values))
            else:
                line = '{}: {}\r\n'.format(key, value)

            sio.write(line)
        sio.write('\r\n')
        sio.flush()

        if enc_msg:
            bio.write(enc_msg)

        return bio.getvalue()

    @property
    def reason(self):
        return self._reason or icap_reasons[self.status_code]

    def encapsulated(self, first_chunk):

        enc_header = []
        enc_msg = b''
        body_type = None

        if self.http_response:
            enc_msg = binary_type(self.http_response)
            enc_header.append('res-hdr=0')
            body_type = 'res-body'
        elif self.http_request:
            enc_msg = binary_type(self.http_request)
            enc_header.append('req-hdr=0')
            body_type = 'req-body'

        body_type = 'null-body' if not first_chunk else body_type
        enc_header.append('{}={}'.format(body_type, len(enc_msg)))

        return enc_header, enc_msg

    def copy(self, icap_request):
        raise NotImplementedError()


class ICAPError(Exception):
    """ Base class for ICAP errors. """


def icap_error(name, status_code):

    def __init__(self, **kw):
        ICAPError.__init__(self, kw.get('reason', None))
        ICAPResponse.__init__(self, status_code, **kw)

    classdict = {'__init__': __init__}

    return type(name, (ICAPError, ICAPResponse), classdict)


OK = partial(ICAPResponse, 200)
NoModificationsNeeded = partial(ICAPResponse, 204)

RequestURITooLong = icap_error(b'RequestURITooLong', 414)
ServiceNotFound = icap_error(b'ServiceNotFound', 404)
MethodNotAllowed = icap_error(b'MethodNotAllowed', 405)
BadComposition = icap_error(b'BadComposition', 418)
