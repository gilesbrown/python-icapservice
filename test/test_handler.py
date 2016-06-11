from six import BytesIO
from icapservice.service import ICAPService
from icapservice.handler import service_abs_path
from icapservice.response import ICAPResponse
from mocksocket import MockSocket

req = b'\r\n'.join((
    b'OPTIONS icap://icap.example.net/nomod ICAP/1.0',
    b'Host: icap.example.net',
    b'User-Agent: BazookaDotCom-ICAP-Client-Library/2.3',
    b'',
    b''
))


class NoMod(ICAPService):

    abs_path = '/nomod'

    def RESPMOD(self, icap_request):
        return ICAPResponse(204)


def test_handle_one_request():

    service = NoMod()
    handler_class = service.handler_class()
    assert service_abs_path(service) in handler_class.service_map

    request = MockSocket(req)
    client_address = object()
    server = object()
    handler_class(request, client_address, server)
    wfile = BytesIO(request.wfile.value)
    assert wfile.readline() == 'ICAP/1.0 200 OK\r\n'
    assert '\nMethods: RESPMOD\r\n' in request.wfile.value
    assert '\nEncapsulated: null-body=0\r\n' in request.wfile.value


def test_handle_one_request_service_not_found():
    service = NoMod()
    service.abs_path = '/notme'
    handler_class = service.handler_class()
    request = MockSocket(req)
    client_address = object()
    server = object()
    handler_class(request, client_address, server)
    wfile = BytesIO(request.wfile.value)
    assert wfile.readline() == 'ICAP/1.0 404 ICAP Service not found\r\n'

