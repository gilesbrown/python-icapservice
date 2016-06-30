from __future__ import print_function, unicode_literals
from six.moves.http_client import HTTPMessage
from six.moves.urllib_parse import urlparse
from copy import deepcopy
from .content import decoders
from .messages import split_start_line, HTTPRequest, HTTPResponse
from .encapsulated import encapsulated_offsets
from .response import (BadComposition,
                       RequestURITooLong,
                       NoModificationsNeeded)


IEOF = object()
CRLF = b'\r\n'

# Maximum from BaseHTTPServer seems reasonable
MAX_REQUEST_LEN = 65536


class ChunkError(Exception):
    """ Something is wrong with the chunks """


class LineReader(object):
    """ Reads lines and keeps track of offset """

    def __init__(self, raw):
        self.raw = raw
        self.offset = 0

    def readline(self, *args, **kwargs):
        line = self.raw.readline(*args, **kwargs)
        self.offset += len(line)
        return line


class ICAPRequest(HTTPMessage):

    def __init__(self, rfile, method, uri, protocol):
        HTTPMessage.__init__(self, rfile)
        self.method = method
        self.uri = uri
        parsed_uri = urlparse(uri)
        self.abs_path = parsed_uri.path
        self.protocol = protocol
        self.preview = self.get('preview') and int(self.get('preview'))
        self.http_request = None
        self.http_response = None
        self.preview_chunks = []
        self.send_continue_after_preview = None
        self.null_body = True
        self.eof = False

    def content_decoder(self):
        if self.http_response:
            encoding = self.http_response.get('content-encoding', 'identity')
        else:
            encoding = self.http_request.get('content-encoding', 'identity')
        return decoders[encoding]

    @property
    def close_connection(self):
        return self.get('connection', '').lower().strip() == 'close'

    def unmodified(self):
        # XXX: check for self.preview is None and then return OK(..., chunks=self.chunks)?
        self.eof = True
        return NoModificationsNeeded()

    def modify_http_request(self, decode=True):
        # we cannot copy the `fp`
        del self.http_request.fp
        http_request = deepcopy(self.http_request)
        if decode:
            decoder = self.content_decoder()
            http_request['content-encoding'] = 'identity'
            chunks = decoder(self.chunks)
        else:
            chunks = self.chunks
        return http_request, chunks

    def modify_http_response(self, decode=True):
        # we cannot copy the `fp`
        del self.http_response.fp
        # remove content-length for modified responses
        del http_response['content-length']
        
        http_response = deepcopy(self.http_response)
        if decode:
            decoder = self.content_decoder()
            http_response['content-encoding'] = 'identity'
            
            chunks = decoder(self.chunks)
        else:
            chunks = self.chunks
        return http_response, chunks

    @classmethod
    def parse(cls, rfile, send_continue_after_preview=None):

        line = rfile.readline(MAX_REQUEST_LEN + 1)
        if not line:
            return None

        if len(line) > MAX_REQUEST_LEN:
            raise RequestURITooLong()

        print(repr(line))
        method, uri, protocol = split_start_line(line)
        request = cls(rfile, method,  uri, protocol)
        request.send_continue_after_preview = send_continue_after_preview
        request.read_encapsulated_http(rfile)
        request.read_preview()
        request.chunks = request._chunks()

        return request

    def read_encapsulated_http(self, rfile):

        encapsulated = self.get('encapsulated')
        if encapsulated is None:
            self.eof = True
            self.null_body = True
            return

        reader = LineReader(rfile)
        for name, offset in encapsulated_offsets(encapsulated):
            if name.endswith('-body'):
                if reader.offset!= offset:
                    reason = "offset '%s' (%d != %d)" % (name, offset, reader.offset)
                    raise BadComposition(reason=reason)
                if name == 'null-body':
                    self.eof = True
                else:
                    self.null_body = False
            elif name == 'req-hdr':
                self.http_request = HTTPRequest.parse(reader)
            elif name == 'res-hdr':
                self.http_response = HTTPResponse.parse(reader)

    def read_preview(self):

        size = self.get('preview')
        if size is None:
            return

        self.preview_chunks = []

        if self.eof:
            return

        for chunk in read_chunks(self.fp):
            if chunk is not IEOF:
                assert not self.eof
                self.preview_chunks.append(chunk)
            else:
                self.eof = True

    def continue_after_preview(self):

        if self.eof:
            return False

        if self.send_continue_after_preview and self.preview is not None:
            self.send_continue_after_preview()
            self.send_continue_after_preview = False

        return True

    def _chunks(self):

        for chunk in self.preview_chunks:
            yield chunk

        if not self.continue_after_preview():
            return

        for chunk in read_chunks(self.fp):
            if chunk is IEOF:
                raise ChunkError("ieof after preview")
            yield chunk


def read_chunks(rfile):

    readline = rfile.readline
    read = rfile.read

    while True:

        chunk_size_line = readline()
        chunk_size, sep, chunk_extension = chunk_size_line.partition(';')
        chunk_size = int(chunk_size, 16)
        if sep == ';':
            if chunk_extension.strip() == 'ieof':
                if int(chunk_size) != 0:
                    raise ChunkError("ieof with non-zero size")
                yield IEOF

        chunk = read(chunk_size)
        crlf = read(2)
        if crlf != CRLF:
            raise ChunkError("found %r expecting CRLF" % crlf)

        if not chunk:
            break

        yield chunk
