from __future__ import print_function, unicode_literals
from six import BytesIO
import pytest
from icapservice.response import BadComposition, RequestURITooLong
from icapservice.request import ICAPRequest, ChunkError, MAX_REQUEST_LEN


respmod_request = (
    b'RESPMOD icap://icap.example.org/satisf ICAP/1.0\r\n'
    b'Host: icap.example.org\r\n'
    b'Encapsulated: req-hdr=0, res-hdr=137, res-body={}\r\n'
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


options_response = (
    b'ICAP/1.0 200 OK\r\n'
    b'Date: Mon, 10 Jan 2000  09:55:21 GMT\r\n'
    b'Methods: RESPMOD\r\n'
    b'Service: FOO Tech Server 1.0\r\n'
    b'ISTag: "W3E4R7U9-L2E4-2"\r\n'
    b'Encapsulated: null-body=0\r\n'
    b'Max-Connections: 1000\r\n'
    b'Options-TTL: 7200\r\n'
    b'Allow: 204\r\n'
    b'Preview: 2048\r\n'
    b'Transfer-Complete: asp, bat, exe, com\r\n'
    b'Transfer-Ignore: html\r\n'
    b'Transfer-Preview: *\r\n'
    b'\r\n'
)

respmod_request_with_preview = (
    b'RESPMOD icap://icap.example.org/satisf ICAP/1.0\r\n'
    b'Preview: 16\r\n'
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
    b'10\r\n'
    b'This is preview.\r\n'
    b'0;{}\r\n'
    b'\r\n'
    b'33{}\r\n'
    b'This is data that was returned by an origin server.{}\n'
    b'0;{}\r\n'
    b'\r\n'
)


def test_request_parse():
    request = ICAPRequest.parse(BytesIO(respmod_request.format(296)))
    assert request.method == b'RESPMOD'
    assert request.protocol == b'ICAP/1.0'


def test_request_parse_wrong_body_offset():
    with pytest.raises(BadComposition):
        ICAPRequest.parse(BytesIO(respmod_request.format(295)))


def test_request_with_null_body():
    request = ICAPRequest.parse(BytesIO(options_response))
    assert request.get('Preview') == '2048'


def test_request_with_preview():
    request = ICAPRequest.parse(BytesIO(respmod_request_with_preview.format('', '', '\r', '')))
    assert request.get('Preview') == '16'
    assert request.preview_chunks == ['This is preview.']
    assert not request.eof


def test_request_with_preview_ieof():

    continued = []
    def continue_after_preview():
        continued.append(True)

    rfile = BytesIO(respmod_request_with_preview.format(' ieof ', '', '\r', ''))
    request = ICAPRequest.parse(rfile, continue_after_preview)
    assert request.get('Preview') == '16'
    assert request.preview_chunks == ['This is preview.']
    assert request.eof
    assert continued == []
    enc_chunks = [chunk for chunk in request.chunks]
    assert continued == []
    assert enc_chunks == request.preview_chunks


def test_request_with_non_zero_ieof():
    rfile = BytesIO(respmod_request_with_preview.format('', '; ieof ', '\r', ''))
    continued = []
    def continue_after_preview():
        continued.append(True)
    request = ICAPRequest.parse(rfile, continue_after_preview)
    with pytest.raises(ChunkError) as excinfo:
        for chunk in request.chunks:
            pass
    assert excinfo.value.message == 'ieof with non-zero size'


def test_request_with_ieof_after_preview():
    rfile = BytesIO(respmod_request_with_preview.format('', '', '\r', 'ieof'))
    request = ICAPRequest.parse(rfile)
    assert request.get('Preview') == '16'
    assert request.preview_chunks == ['This is preview.']
    assert not request.eof
    with pytest.raises(ChunkError) as excinfo:
        for chunk in request.chunks:
            pass
    assert excinfo.value.message == 'ieof after preview'


def test_request_missing_cr_after_chunk():
    continued = []
    def continue_after_preview():
        continued.append(True)
    rfile = BytesIO(respmod_request_with_preview.format('', '', '', ''))
    request = ICAPRequest.parse(rfile, continue_after_preview)
    with pytest.raises(ChunkError) as excinfo:
        for chunk in request.chunks:
            pass
    assert excinfo.value.message.endswith(' expecting CRLF')

format_request_line = b'REQMOD /{} ICAP/1.0\r\n\n'.format


def test_parse():
    rfile = BytesIO(format_request_line('abc'))
    icap_request = ICAPRequest.parse(rfile)
    assert icap_request.uri == '/abc'

def test_max_request_len():
    rfile = BytesIO(format_request_line('a' * MAX_REQUEST_LEN))
    with pytest.raises(RequestURITooLong):
        ICAPRequest.parse(rfile)
