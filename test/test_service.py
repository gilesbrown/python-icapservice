from six import BytesIO
from six.moves.http_client import HTTPMessage
from icapuchin import ICAPService
from icapuchin.messages import split_start_line


options_request = (
    b'OPTIONS icap://127.0.0.1:1344/respmod ICAP/1.0\r\n'
    b'Host: 127.0.0.1:1344\r\n'
    b'Connection: close\r\n'
    b'Allow: 206\r\n'
)


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


def respond(request):
    rfile = BytesIO(request)
    wfile = BytesIO()
    service = ICAPService()
    close_socket = service.respond(rfile, wfile)
    wfile.seek(0)
    return close_socket, service, wfile


def test_methods():
    service = ICAPService()
    assert service.methods() == ['RESPMOD']


def test_options():
    close_socket, app, wfile = respond(options_request)
    assert close_socket
    protocol, status_code, reason = split_start_line(wfile.readline())
    assert protocol == 'ICAP/1.0'
    assert int(status_code) == 200
    assert reason == 'OK'
    headers = HTTPMessage(wfile)
    assert headers.get('Encapsulated') == 'null-body=0'


def test_respmod():
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


def test_respmod_with_preview():
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


def test_handle_socket(monkeypatch):

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


def test_respond_eof():
    rfile = BytesIO()
    wfile = BytesIO()
    service = ICAPService()
    close_socket = service.respond(rfile, wfile)
    assert close_socket == True


def test_write_unmodified():
    wfile = BytesIO()
    service = ICAPService()
    service.write_unmodified(wfile)
    assert wfile.getvalue() == 'ICAP/1.0 204 No modifications needed\r\n\r\n'
