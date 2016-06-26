from __future__ import print_function, unicode_literals
from uuid import uuid4
from six import BytesIO
from six.moves.http_client import responses as http_reasons
from .response import ICAPResponse, ICAPResponseHeaders
from .handler import ICAPRequestHandler
from .messages import HTTPResponse


class ICAPService(object):

    # See: https://tools.ietf.org/html/rfc3507#section-4.10.2
    default_options_headers = {
        'Preview': 0,
        'Transfer-Preview': '*',
        'Transfer-Ignore': ['jpg', 'jpeg', 'gif', 'png', 'swf', 'flv', 'ico'],
        'Transfer-Complete': [],
        'Max-Connections': 1000,
        'Options-TTL': 7200,
    }

    # List of all possible ICAP method (excluding OPTIONS).
    # The RFC allows allows for adding new methods as server extensions.
    # If you do want to to this then just append the names to this list.
    # See https://tools.ietf.org/html/rfc3507#section-4.3.2 for details.
    icap_methods = ['REQMOD', 'RESPMOD']

    # The `Abs_Path` section of the URI for this service, as per
    # `https://tools.ietf.org/html/rfc3507#section-4.2`.
    abs_path = None

    def __init__(self):
        self.options_headers = self.default_options_headers.copy()
        self.options_headers['Methods'] = []
        for method in self.icap_methods:
            if hasattr(self, method):
                self.options_headers['Methods'].append(method)
        self.response_headers = ICAPResponseHeaders()
        self.istag = uuid4().hex

    def _get_istag(self):
        return self.response_headers.get('istag')

    def _set_istag(self, value):
        self.response_headers['istag'] = value

    istag = property(_get_istag, _set_istag)

    def new_http_response(self, status_code, protocol=None, reason=None):
        if not reason:
            reason = http_reasons[status_code]
        if not protocol:
            protocol = 'HTTP/1.1'
        fp = BytesIO(b'{} {} {}\r\n\r\n'.format(protocol, status_code, reason))
        return HTTPResponse.parse(fp)

    def icap_handler_class(self, **kwargs):
        """ Return a new request handler class for just this service. """
        return ICAPRequestHandler.for_services([self], **kwargs)

    def OPTIONS(self, request):
        return ICAPResponse(200, headers=self.options_headers)
