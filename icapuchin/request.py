from __future__ import print_function, unicode_literals
from six.moves.http_client import HTTPMessage
from .messages import split_start_line, Request, Response
from .encapsulated import encapsulated_offsets, EncapsulationError
from .response import ICAPResponse


IEOF = object()
CRLF = b'\r\n'


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
        self.rfile = rfile
        self.method = method
        self.uri = uri
        self.protocol = protocol
        self.preview = self.get('Preview') and int(self.get('Preview'))
        self.encapsulated_request = None
        self.encapsulated_response = None
        self.body_chunks = []
        self.null_body = True
        self.eof = False

        reader = LineReader(self.rfile)
        for name, offset in encapsulated_offsets(self):
            if name.endswith('-body'):
                if reader.offset!= offset:
                    raise EncapsulationError("offset '%s' (%d != %d)" %
                                             (name, offset, reader.offset))
                if name == 'null-body':
                    self.eof = True
                else:
                    self.null_body = False
            elif name == 'req-hdr':
                self.encapsulated_request = Request.from_rfile(reader)
            elif name == 'res-hdr':
                self.encapsulated_response = Response.from_rfile(reader)

        if self.preview is not None and not self.eof:
            for chunk in self.read_chunks():
                if chunk is not IEOF:
                    self.body_chunks.append(chunk)
                else:
                    self.eof = True

    @classmethod
    def from_rfile(cls, rfile):

        line = rfile.readline()
        if not line:
            return None

        method, uri, protocol = split_start_line(line)
        request = cls(rfile, method,  uri, protocol)

        return request

    def read_chunks(self):

        readline = self.rfile.readline
        read = self.rfile.read

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

            if chunk:
                yield chunk
            else:
                break

    def encapsulated_chunks(self, wfile):

        if self.preview is not None and not self.eof:
            ICAPResponse.write_100(wfile)

        for chunk in self.body_chunks:
            yield chunk

        if self.eof:
            return

        for chunk in self.read_chunks():
            if chunk is IEOF:
                raise ChunkError("should not see ieof after preview")
            yield chunk
