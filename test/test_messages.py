from six import BytesIO, binary_type
from icapuchin.messages import Request, Response

request_bytes = (
    b'POST /something HTTP/1.1\r\n'
    b'Content-Type: really/something\r\n'
    b'Content-Length: 3\r\n'
    b'\r\n'
    b'123'
)

response_bytes = (
    b'HTTP/1.1 200 OK\r\n'
    b'Content-Type: something/else\r\n'
    b'Content-Length: 3\r\n'
    b'\r\n'
    b'456'
)


def test_request_bytes():
    request = Request.from_rfile(BytesIO(request_bytes))
    # bytes does not include the content!
    assert binary_type(request) == request_bytes[:-3]


def test_response_bytes():
    response = Response.from_rfile(BytesIO(response_bytes))
    # bytes does not include the content!
    assert binary_type(response) == response_bytes[:-3]
