import os
from glob import glob
from pkg_resources import resource_filename
from contextlib import closing
from collections import namedtuple
from six import BytesIO
from six.moves.http_client import HTTPMessage
import pytest

from icapservice import ICAPService, OK, NoModificationsNeeded
from mocksocket import MockSocket





def read_example(filename):

    class _bytearray(bytearray):
        """ Derive a class so we can add attributes. """

    request = _bytearray()
    request.id = os.path.basename(filename)
    response = _bytearray()
    response.id = 'expected_response'
    section = 0
    with open(filename, 'rb') as fp:
        for line in fp:
            if line.startswith('-' * 10):
                section += 1
            else:
                if section == 0:
                    pass  # request title
                elif section == 1:
                    request.extend(line)
                elif section == 2:
                    pass  # response title
                elif section == 3:
                    response.extend(line)

    return request, response


class Example1(ICAPService):

    abs_path = '/server'
    persistent_connections = False

    def __init__(self):
        super(Example1, self).__init__()
        self.istag = '"W3E4R7U9-L2E4-2"'
        self.response_headers['server'] = 'ICAP-Server-Software/1.0'

    def REQMOD(self, icap_request):
        http_request = icap_request.modify_http_request()
        http_request.uri = '/modified-path'
        http_request['via'] = '1.0 icap-server.net (ICAP Example ReqMod Service 1.1)'
        http_request['accept-encoding'] = 'gzip, compress'
        http_request['accept'] = http_request['accept'] + ', image/gif'
        del http_request['cookie']
        return OK(http_request=http_request)


class Example2(ICAPService):

    abs_path = '/server'
    persistent_connections = False

    def __init__(self):
        super(Example2, self).__init__()
        self.istag = '"W3E4R7U9-L2E4-2"'
        self.response_headers['server'] = 'ICAP-Server-Software/1.0'

    def REQMOD(self, icap_request):
        http_request = icap_request.modify_http_request()
        http_request['via'] = '1.0 icap-server.net (ICAP Example ReqMod Service 1.1)'
        http_request['accept-encoding'] = 'gzip, compress'
        http_request['content-length'] = '45'
        http_request['accept'] = http_request['accept'] + ', image/gif'

        def new_chunks(icap_request):
            for chunk in icap_request.chunks:
                yield chunk.replace('this information.', 'this information.' + '  ICAP powered!')

        chunks = new_chunks(icap_request)

        return OK(http_request=http_request, chunks=chunks)


class Example3(ICAPService):

    persistent_connections = False
    abs_path = '/content-filter'

    def __init__(self):
        super(Example3, self).__init__()
        self.istag = '"W3E4R7U9-L2E4-2"'
        self.response_headers['server'] = 'ICAP-Server-Software/1.0'

    def REQMOD(self, icap_request):
        http_response = self.new_http_response(403)
        http_response.status_code = 403
        #http_response.protocol = 'HTTP/1.1'
        #http_response.reason = 'Forbidden'
        http_response['Server'] = 'Apache/1.3.12 (Unix)'
        http_response['Last-Modified'] = 'Thu, 02 Nov 2000 13:51:37 GMT'
        http_response['Date'] = 'Wed, 08 Nov 2000 16:02:10 GMT'
        http_response['ETag'] = '"63600-1989-3a017169"'
        http_response['Content-Length'] = '58'
        http_response['Content-Type'] = 'text/html'
        chunks = ('Sorry, you are not allowed to access that naughty content.',)
        return OK(http_response=http_response, chunks=chunks)


class Example4(ICAPService):

    persistent_connections = False
    abs_path = '/satisf'

    def __init__(self):
        super(Example4, self).__init__()
        self.istag = '"W3E4R7U9-L2E4-2"'
        self.response_headers['server'] = 'ICAP-Server-Software/1.0'

    def RESPMOD(self, icap_request):
        http_response = icap_request.modify_http_response()
        http_response['via'] = '1.0 icap.example.org (ICAP Example RespMod Service 1.1)'
        http_response['Date'] = 'Mon, 10 Jan 2000 09:55:21 GMT'
        def new_chunks(icap_request):
            for chunk in icap_request.chunks:
                yield chunk.replace('origin server.', 'origin server, but with\r\nvalue added by an ICAP server.')
        return OK(http_response=http_response, chunks=new_chunks(icap_request))


class Example5(ICAPService):

    abs_path = '/sample-service'
    persistent_connections = True

    def __init__(self):
        ICAPService.__init__(self)
        self.istag = '"W3E4R7U9-L2E4-2"'
        self.options_headers['Service'] = 'FOO Tech Server 1.0'
        self.options_headers['Preview'] = 2048
        self.options_headers['Transfer-Complete'] = ['asp', 'bat', 'exe', 'com']
        self.options_headers['Transfer-Ignore'] = ['html']
        self.options_headers['Allow'] = [204]

    # define this so ICAPService will add it to options_headers['Methods']
    def RESPMOD(self, icap_request):
        return NoModificationsNeeded()


example_services = {
    1: Example1,
    2: Example2,
    3: Example3,
    4: Example4,
    5: Example5,
}


def respond(request_bytes, service_class):
    request = MockSocket(request_bytes)
    client_address = object()
    service = service_class()
    handler_class = service.handler_class(persistent_connections=service.persistent_connections)
    handler_class(request, client_address)
    assert request.wfile.closed
    return request.wfile.value


def handle_request(example_no, request):
    return respond(request, example_services[example_no])


Message = namedtuple('Message', 'icap_msg enc_msg_1 enc_msg_2 chunks')


def parse_msg(fp):
    status = fp.readline()
    msg = HTTPMessage(fp)
    msg.status = status
    return msg


def parse_enc(fp, offset):
    if not offset or offset[0].startswith('null-'):
        return None
    return parse_msg(fp)


def parse_icap_response(data):
    with closing(BytesIO(data)) as fp:
        icap_status = fp.readline()
        icap_msg = HTTPMessage(fp)
        icap_msg.status = icap_status
        enc_header = icap_msg.get('encapsulated')
        enc_offsets = [offset.strip() for offset in enc_header.split(',')]
        enc_msg_1 = parse_enc(fp, enc_offsets[:1])
        enc_msg_2 = parse_enc(fp, enc_offsets[1:])
        chunks = fp.read()
    return Message(icap_msg, enc_msg_1, enc_msg_2, chunks)


def compare_icap_headers(expected, actual):
    assert sorted(expected.keys()) == sorted(actual.keys())
    for k in expected.keys():
        assert expected[k] == actual[k]


def compare_enc(expected, actual):
    assert (expected is not None and actual is not None) or (expected is None and actual is None)
    if expected is None:
        return
    assert sorted(expected.keys()) == sorted(actual.keys())
    for k in expected.keys():
        assert expected[k] == actual[k]


def compare_response(expected_bytes, actual_bytes):
    expected = parse_icap_response(expected_bytes)
    actual = parse_icap_response(actual_bytes)
    assert expected.icap_msg.status == actual.icap_msg.status
    compare_icap_headers(expected.icap_msg, actual.icap_msg)
    compare_enc(expected.enc_msg_1, actual.enc_msg_1)
    compare_enc(expected.enc_msg_2, actual.enc_msg_2)
    assert expected.chunks == actual.chunks


def read_examples():
    dirname = resource_filename(__name__, 'rfc_examples')
    filenames = glob(os.path.join(dirname, '*_Example_?'))
    return [read_example(filename) for filename in filenames]


@pytest.mark.parametrize("test_example,expected_response",
                         read_examples(),
                         ids=lambda obj: getattr(obj, 'id', None))
def test_rfc_example(monkeypatch, test_example, expected_response):
    def now_rfc1123():
        return 'Mon, 10 Jan 2000  09:55:21 GMT'
    monkeypatch.setattr('icapservice.response.now_rfc1123', now_rfc1123)
    example_no = int(test_example.id.rpartition('_')[2])
    response = handle_request(example_no, test_example)
    compare_response(expected_response, response)
