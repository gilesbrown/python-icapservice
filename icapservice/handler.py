from __future__ import print_function, unicode_literals
import socket
import logging
from itertools import chain
from six import binary_type
from six.moves.socketserver import (StreamRequestHandler,
                                    ThreadingMixIn,
                                    ForkingMixIn)
from six.moves import BaseHTTPServer
from .request import ICAPRequest
from .response import ICAPResponse, ServiceNotFound, MethodNotAllowed


FINAL_CHUNK = b'0\r\n\r\n'


def service_abs_path(service):
    return service.abs_path or '/' + service.__class__.__name__


class ICAPServer(BaseHTTPServer.HTTPServer):
    """ ICAP Server. """


class ThreadingICAPServer(ThreadingMixIn, ICAPServer):
    """ ICAP Server using threading. """


class ForkingICAPServer(ForkingMixIn, ICAPServer):
    """ ICAP Server using forking. """


class ICAPRequestHandler(StreamRequestHandler):
    """ Handler for ICAP requests.  """

    #: Map of `Abs_Path` to `ICAPService` (or similar) objects.
    #: This map should defined in derived classes.
    #: The easiest way to do this is using `ICAPRequestHandler.for_services`.
    service_map = None

    #: Response headers.
    response_headers = None

    log = None

    # The server=None default is to support `gevent.server.StreamServer`
    def __init__(self, request, client_address, server=None):
        StreamRequestHandler.__init__(self, request, client_address, server)

    @classmethod
    def for_services(cls, services, **kwargs):
        """ Create a new handler class for the specified ICAP services. """
        name = binary_type('ICAPServicesRequestHandler')
        bases = (cls, object)
        service_map = {service_abs_path(service):
                       service for service in services}
        classdict = {
            'service_map': service_map,
            'log': logging.getLogger(__name__),
            'persistent_connections': True,
        }
        classdict.update(kwargs)
        return type(name, bases, classdict)


    def handle_one_request(self):
        """ Handle a single ICAP request. """

        icap_response = None
        icap_request = None

        try:

            icap_request = ICAPRequest.parse(self.rfile,
                                             self.continue_after_preview)
            if icap_request is None:
                return

            service = self.service_map.get(icap_request.abs_path)
            if service is None:
                icap_response = ServiceNotFound()
                return

            if (icap_request.method not in service.icap_methods and
                icap_request.method != 'OPTIONS'):
                icap_response = MethodNotAllowed()
                return

            method = getattr(service, icap_request.method, None)
            if method is None:
                icap_response = MethodNotAllowed()
                return

            icap_response = method(icap_request)
            icap_response.headers.merge(service.response_headers or {})

            if self.persistent_connections:
                self.close_connection = icap_request.close_connection
            else:
                self.close_connection = True


        except socket.timeout as exc:

            self.log.error("request timed out: %r", exc)
            self.close_connection = 1

        finally:

            if icap_response is not None:
                self.respond(icap_request, icap_response)
            else:
                self.close_connection = 1

            if icap_request:
                # consume any remaining chunks
                for chunk in icap_request.chunks:
                    pass

    def handle(self):
         """Handle multiple requests if necessary."""
         self.close_connection = 0

         self.handle_one_request()
         while not self.close_connection:
             self.handle_one_request()

    def respond(self, icap_request, icap_response):

        if isinstance(icap_response, int):
            icap_response = ICAPResponse(icap_response)

        icap_response.headers.merge(self.response_headers or {})
        if self.close_connection:
            icap_response.headers['Connection'] = 'close'

        self.log.info('"%s %s" - %s',
                      icap_request.method,
                      icap_request.abs_path,
                      icap_response.status_code)

        chunks = iter(icap_response.chunks)
        try:
            first_chunk = [next(chunks)]
        except StopIteration:
            first_chunk = []

        header_bytes = icap_response.header_bytes(first_chunk)

        self.wfile.write(header_bytes)

        for chunk in chain(first_chunk, chunks):
            formatted = b'{:x}\r\n{}\r\n'.format(len(chunk), chunk)
            self.wfile.write(formatted)

        if first_chunk:
            self.wfile.write(FINAL_CHUNK)

    def continue_after_preview(self):
        self.respond(100)

    @classmethod
    def server(cls, server_class=None, server_address=None, **server_kwargs):
        """ Return a new server instance using this handler class.

        The server instantiated using the `SocketServer` protocol:

            SocketServer(server_address, handler_class, **server_kwargs)

        Typical use does not require `server_kwargs`.
        """
        if server_class is None:
            server_class = ICAPServer
        if server_address is None:
            server_address = ('127.0.0.1', 1344)
        return server_class(server_address, cls, **server_kwargs)
