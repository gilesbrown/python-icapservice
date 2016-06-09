from six import BytesIO
from six.moves.http_client import HTTPMessage
from icapservice import ICAPService, NoModificationsNeeded, OK
from icapservice.messages import split_start_line
from mocksocket import MockSocket



respmod_request = (
    b'RESPMOD icap://icap.example.org/satisf ICAP/1.0\r\n'
    b'Host: icap.example.org\r\n'
    b'Encapsulated: req-hdr=0, res-hdr=137, res-body=296\r\n'
    b'\r\n'
    b'GET /origin-resource HTTP/1.1\r\n'
    b'Host: www.origin-server.com\r\n'
    b'Accept: text/html, text/plain, image/gif\r\n'
    b'Accept-Encoding: gzip, compress\r\n'
    b'\r\n'
    b'HTTP/1.1 200 OK\r\n'
    b'Date: Mon, 10 Jan 2000 09:52:22 GMT\r\n'
    b'Server: Apache/1.3.6 (Unix)\r\n'
    b'ETag: "63840-1ab7-378d415b"\r\n'
    b'Content-Type: text/html\r\n'
    b'Content-Length: 51\r\n'
    b'\r\n'
    b'33\r\n'
    b'This is data that was returned by an origin server.\r\n'
    b'0\r\n'
    b'\r\n'
)


respmod_with_preview_request = (
    b'RESPMOD icap://icap.example.org/satisf ICAP/1.0\r\n'
    b'Preview: 0\r\n'
    b'Host: icap.example.org\r\n'
    b'Encapsulated: req-hdr=0, res-hdr=137, res-body=296\r\n'
    b'\r\n'
    b'GET /origin-resource HTTP/1.1\r\n'
    b'Host: www.origin-server.com\r\n'
    b'Accept: text/html, text/plain, image/gif\r\n'
    b'Accept-Encoding: gzip, compress\r\n'
    b'\r\n'
    b'HTTP/1.1 200 OK\r\n'
    b'Date: Mon, 10 Jan 2000 09:52:22 GMT\r\n'
    b'Server: Apache/1.3.6 (Unix)\r\n'
    b'ETag: "63840-1ab7-378d415b"\r\n'
    b'Content-Type: text/html\r\n'
    b'Content-Length: 51\r\n'
    b'\r\n'
    b'0\r\n'
    b'\r\n'
    b'33\r\n'
    b'This is data that was returned by an origin server.\r\n'
    b'0\r\n'
    b'\r\n'
)


class ReqMod(ICAPService):

    def REQMOD(self, request):
        return NoModificationsNeeded()


def respond(request_bytes, service_class):
    request = MockSocket(request_bytes)
    client_address = object()
    service = service_class()
    handler_class = service.handler_class()
    handler_class(request, client_address)
    assert request.wfile.closed
    return request.wfile.value


class REQMODExampleService1(ICAPService):

    abs_path = '/server'

    def REQMOD(self, request):
        return OK()



class OptionsExample5(ICAPService):

    abs_path = '/sample-service'

    def __init__(self):
        ICAPService.__init__(self)
        self.options_headers['Service'] = 'FOO Tech Server 1.0'
        self.options_headers['Preview'] = 2048
        self.options_headers['Transfer-Complete'] = ['asp', 'bat', 'exe', 'com']
        self.options_headers['Transfer-Ignore'] = ['html']
        self.options_headers['Allow'] = [204]

    # define this so ICAPService will add it to options_headers['Methods']
    def RESPMOD(self, request):
        return NoModificationsNeeded()


def test_reqmod_example_1():

    # https://tools.ietf.org/html/rfc3507#section-4.8.3

    enc_request =  b'\r\n'.join((
        b'GET / HTTP/1.1',
        b'Host: www.origin-server.com',
        b'Accept: text/html, text/plain',
        b'Accept-Encoding: compress',
        b'Cookie: ff39fk3jur@4ii0e02i',
        b'If-None-Match: "xyzzy", "r2d2xxxx"'
    ))


    request_bytes = b'\r\n'.join((
        b'REQMOD icap://icap-server.net/server?arg=87 ICAP/1.0',
        b'Host: icap-server.net',
        b'Encapsulated: req-hdr=0, null-body={}',
        b'',
        b'{}',
    )).format(len(enc_request), enc_request)

    response_bytes = respond(request_bytes, REQMODExampleService1)

    response = BytesIO(response_bytes)

    icap_status_line = response.readline()
    assert icap_status_line == 'ICAP/1.0 200 OK\r\n'
    #icap_headers = HTTPMessage(response)

    #enc_request_line = response.readline()
    #enc_headers = HTTPMessage(response)

#    ----------------------------------------------------------------
#    ICAP Request Modification Example 1 - ICAP Response
#    ----------------------------------------------------------------
#    ICAP/1.0 200 OK
#    Date: Mon, 10 Jan 2000  09:55:21 GMT
#    Server: ICAP-Server-Software/1.0
#    Connection: close
#    ISTag: "W3E4R7U9-L2E4-2"
#    Encapsulated: req-hdr=0, null-body=231
# 
#    GET /modified-path HTTP/1.1
#    Host: www.origin-server.com
#    Via: 1.0 icap-server.net (ICAP Example ReqMod Service 1.1)
#    Accept: text/html, text/plain, image/gif
#    Accept-Encoding: gzip, compress
#    If-None-Match: "xyzzy", "r2d2xxxx"
# 


def test_options_example_5():

    # https://tools.ietf.org/html/rfc3507#section-4.3.10
    request_bytes = b'\r\n'.join((
        b'OPTIONS icap://icap.server.net/sample-service ICAP/1.0',
        b'Host: icap.server.net',
        b'User-Agent: BazookaDotCom-ICAP-Client-Library/2.3',
        b''
        b''
    ))

    response_bytes = respond(request_bytes, OptionsExample5)

    response = BytesIO(response_bytes)
    status_line = response.readline()
    assert status_line == b'ICAP/1.0 200 OK\r\n'
    headers = HTTPMessage(response)
    assert headers.get('date')
    assert headers.get('methods') == 'RESPMOD'
    assert headers.get('service') == 'FOO Tech Server 1.0'
    assert len(headers.get('istag')) == 32
    assert headers.get('encapsulated') == 'null-body=0'
    assert headers.get('max-connections') == '1000'
    assert headers.get('options-ttl') == '7200'
    assert headers.get('allow') == '204'
    assert headers.get('preview') == '2048'
    assert headers.get('transfer-complete') == 'asp, bat, exe, com'
    assert headers.get('transfer-ignore') == 'html'
    assert headers.get('transfer-preview') == '*'


def Xtest_respmod():
    close_socket, app, wfile = respond(respmod_request)
    assert not close_socket
    protocol, status_code, reason = split_start_line(wfile.readline())
    assert protocol == 'ICAP/1.0'
    assert int(status_code) == 200
    assert reason == 'OK'

    icap_headers = HTTPMessage(wfile)
    assert icap_headers.get('Encapsulated') == 'res-hdr=0, res-body=159'
    check_encapsulated(wfile)


def check_encapsulated(wfile):
    pos_before = wfile.tell()
    protocol, status_code, reason = split_start_line(wfile.readline())
    assert protocol == 'HTTP/1.1'
    assert status_code == '200'
    assert reason == 'OK'
    enc_res_hdrs = HTTPMessage(wfile)
    assert enc_res_hdrs.get('Content-Type') == 'text/html'
    pos_after = wfile.tell()
    assert pos_after - pos_before == 159
    chunk_size_line = wfile.readline()
    assert chunk_size_line == '33\r\n'
    chunk_size = int(chunk_size_line, 16)
    assert chunk_size == 51
    chunk = wfile.read(chunk_size)
    assert chunk == 'This is data that was returned by an origin server.'
    assert wfile.read() == '\r\n0\r\n\r\n'


def Xtest_respmod_with_preview():
    close_socket, app, wfile = respond(respmod_with_preview_request)
    assert not close_socket
    protocol, status_code, reason = split_start_line(wfile.readline())
    assert protocol == 'ICAP/1.0'
    assert int(status_code) == 100
    assert reason == 'Continue after ICAP Preview'

    headers_100 = HTTPMessage(wfile)
    assert not headers_100

    protocol, status_code, reason = split_start_line(wfile.readline())
    assert protocol == 'ICAP/1.0'
    assert int(status_code) == 200
    assert reason == 'OK'

    icap_headers = HTTPMessage(wfile)
    assert icap_headers.get('Encapsulated') == 'res-hdr=0, res-body=159'
    check_encapsulated(wfile)


def Xtest_handle_socket(monkeypatch):

    respond_calls = []

    rfile = BytesIO()
    wfile = BytesIO()

    class Socket(object):
        closed = False
        def close(self):
            self.closed = True
        def makefile(self, mode):
            assert mode in ('rb', 'wb')
            if mode == 'rb':
                return rfile
            else:
                return wfile


    socket = Socket()
    address = ('127.0.0.1', 54321)

    def respond(self, r, w):
        assert self is service
        assert r is rfile
        assert w is wfile
        respond_calls.append(self)
        return True

    monkeypatch.setattr(ICAPService, 'respond', respond)
    service = ICAPService()
    service.handle_socket(socket, address)


def Xtest_respond_eof():
    rfile = BytesIO()
    wfile = BytesIO()
    service = ICAPService()
    close_socket = service.respond(rfile, wfile)
    assert close_socket == True


def Xtest_write_unmodified():
    wfile = BytesIO()
    service = ICAPService()
    service.write_unmodified(wfile)
    assert wfile.getvalue() == 'ICAP/1.0 204 No modifications needed\r\n\r\n'
