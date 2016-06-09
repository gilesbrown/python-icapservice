import os
from glob import glob
from pkg_resources import resource_filename
from contextlib import closing
from collections import namedtuple
from six import binary_type, BytesIO
from six.moves.http_client import HTTPMessage
import pytest

from icapservice import ICAPService
from mocksocket import MockSocket


def read_examples():
    dirname = resource_filename(__name__, 'rfc_examples')
    filenames = glob(os.path.join(dirname, '*_Example_?'))
    return [read_example(filename) for filename in filenames][:1]



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

    return request, binary_type(response)


Message = namedtuple('Message', 'icap_status icap_headers enc_1 enc_2')


def parse_icap_response(data):
    with closing(BytesIO(data)) as fp:
        icap_status = fp.readline()
        icap_message = HTTPMessage(fp)
        enc_header = icap_message.get('encapsulated')
        enc_parts = [p.partition('=')[0].strip() for p in enc_header.split(',')]
        enc = []
        for p in enc_parts:
            if p.startswith('null-'):
                enc.append(None)
            else:
                enc.append(HTTPMessage(fp))
    return Message(icap_status, icap_message, *enc)


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
        print expected[k], actual[k]
        assert expected[k] == actual[k]


def compare_response(expected_bytes, actual_bytes):
    expected = parse_icap_response(expected_bytes)
    actual = parse_icap_response(actual_bytes)
    assert expected.icap_status == actual.icap_status
    compare_icap_headers(expected.icap_headers, actual.icap_headers)
    compare_enc(expected.enc_1, actual.enc_1)
    compare_enc(expected.enc_2, actual.enc_2)


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



class ServiceExample1(ICAPService):

    abs_path = '/server'
    persistent_connections = False

    def __init__(self):
        super(ServiceExample1, self).__init__()
        self.istag = '"W3E4R7U9-L2E4-2"'
        self.response_headers['server'] = 'ICAP-Server-Software/1.0'

    def REQMOD(self, icap_request):
        icap_response = icap_request.reqmod()
        icap_response.http_request.uri = '/modified-path'
        return icap_response

example_services = {
    1: ServiceExample1,
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
