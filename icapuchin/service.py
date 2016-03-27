from __future__ import print_function, unicode_literals
from contextlib import closing
from uuid import uuid4
from .request import ICAPRequest
from .response import ICAPResponse


class ICAPService(object):

    # See: https://tools.ietf.org/html/rfc3507#section-4.10.1
    OPTIONS = {
        'ISTag': uuid4().hex,
        'Service': 'ICAPuchin Service 1.0',
        'Preview': 0,
        'Transfer-Preview': '*',
        'Transfer-Ignore': ['jpg', 'jpeg', 'gif', 'png', 'swf', 'flv', 'ico'],
        'Transfer-Complete': [],
        'Max-Connections': 1000,
        'Options-TTL': 3600,
    }

    new_request_from_rfile = ICAPRequest.from_rfile

    def handle_socket(self, socket, address):
        close_socket = True
        try:
            while True:
                with closing(socket.makefile('rb')) as rfile:
                    with closing(socket.makefile('wb')) as wfile:
                        close_socket = self.respond(rfile, wfile)
                if close_socket:
                    break
        finally:
            if close_socket:
                socket.close()

    def respond(self, rfile, wfile):
        request = self.new_request_from_rfile(rfile)
        if request is not None:
            connection_header = request.get('Connection', '')
            close_socket = (connection_header.strip().lower() == 'close')
            method = getattr(self, 'do_%s' % request.method)
            method(request, wfile)
        else:
            close_socket = True
        return close_socket

    def methods(self):
        methods = set(name[3:] for name in dir(self) if name.startswith('do_'))
        # as per 4.10.2 - OPTIONS must not by in our methods list
        methods.remove('OPTIONS')
        return list(methods)

    def options(self):
        options = dict(self.OPTIONS)
        options['Methods'] = self.methods()
        return options

    def do_OPTIONS(self, request, wfile):
        headers = self.options()
        ICAPResponse(200, headers=headers).write(wfile, ())

    def do_RESPMOD(self, request, wfile):
        # ICAPResponse.write_204(wfile)
        self.write_chunks(wfile,
                          request.null_body,
                          request.encapsulated_chunks(wfile),
                          encapsulated_response=request.encapsulated_response)

    def write_unmodified(self, wfile):
        ICAPResponse.write_204(wfile)

    def write_chunks(self, wfile, null_body, chunks, **kw):
        response = ICAPResponse(200, **kw)
        response.write(wfile, chunks)
