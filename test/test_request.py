from __future__ import print_function, unicode_literals
from six import BytesIO
import pytest
from icapuchin.request import (ICAPRequest,
                               EncapsulationError,
                               ChunkError)


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
    b'0\r\n'
    b'\r\n'
)


def test_request_from_rfile():
    request = ICAPRequest.from_rfile(BytesIO(respmod_request.format(296)))
    assert request.method == b'RESPMOD'
    assert request.protocol == b'ICAP/1.0'


def test_request_from_rfile_wrong_body_offset():
    with pytest.raises(EncapsulationError):
        ICAPRequest.from_rfile(BytesIO(respmod_request.format(295)))


def test_request_with_null_body():
    request = ICAPRequest.from_rfile(BytesIO(options_response))
    assert request.get('Preview') == '2048'


def test_request_with_preview():
    request = ICAPRequest.from_rfile(BytesIO(respmod_request_with_preview.format('', '', '\r')))
    assert request.get('Preview') == '16'
    assert request.body_chunks == ['This is preview.']
    assert not request.eof


def test_request_with_preview_ieof():
    request = ICAPRequest.from_rfile(BytesIO(respmod_request_with_preview.format(' ieof ', '', '\r')))
    assert request.get('Preview') == '16'
    assert request.body_chunks == ['This is preview.']
    assert request.eof
    wfile = BytesIO()
    enc_chunks = [chunk for chunk in request.encapsulated_chunks(wfile)]
    assert enc_chunks == request.body_chunks


def test_request_with_non_zero_ieof():
    request = ICAPRequest.from_rfile(BytesIO(respmod_request_with_preview.format('', '; ieof ', '\r')))
    with pytest.raises(ChunkError) as excinfo:
        wfile = BytesIO()
        for chunk in request.encapsulated_chunks(wfile):
            pass
    assert excinfo.value.message == 'ieof with non-zero size'


def test_request_missing_cr_after_chunk():
    request = ICAPRequest.from_rfile(BytesIO(respmod_request_with_preview.format('', '', '')))
    with pytest.raises(ChunkError) as excinfo:
        wfile = BytesIO()
        for chunk in request.encapsulated_chunks(wfile):
            pass
    assert excinfo.value.message.endswith(' expecting CRLF')
