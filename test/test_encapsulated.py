from __future__ import print_function, unicode_literals
from six import BytesIO
from six.moves.http_client import HTTPMessage
import pytest
from icapuchin.encapsulated import encapsulated_offsets, EncapsulationError


def check(offsets):
    value = ' , '.join('{} = {}'.format(n, o) for n, o in offsets)
    header = 'Encapsulated: {} '.format(value)
    rfile = BytesIO(header + '\r\n\r\n')
    request = HTTPMessage(rfile)
    assert encapsulated_offsets(request) == offsets


def test_encapsulated_offsets_opt_body():
    offsets = [('opt-body', 0)]
    check(offsets)


def test_encapsulated_offsets_req_body():
    offsets = [('req-body', 0)]
    check(offsets)


def test_encapsulated_offsets_respmod_request():
    offsets = [('req-hdr', 0), ('res-hdr', 1), ('res-body', 2)]
    check(offsets)


def test_encapsulated_offsets_respmod_response():
    offsets = [('res-hdr', 1), ('res-body', 2)]
    check(offsets)


def test_encapsulated_offsets_null_body():
    offsets = [('null-body', 0)]
    check(offsets)


def test_encapsulation_wrong_name():
    offsets = [('no-body', 0)]
    with pytest.raises(EncapsulationError):
        check(offsets)


def test_encapsulated_header_not_present():
    request = HTTPMessage(BytesIO())
    assert encapsulated_offsets(request) == []


def test_encapsulated_header_offsets_wrong_order():
    offsets = [('res-hdr', 2), ('res-body', 1)]
    with pytest.raises(EncapsulationError):
        check(offsets)
