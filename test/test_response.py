import pytest
from icapservice import response


def test_icap_response():
    resp = response.ICAPResponse()
    assert resp.status_code == 200
    assert resp.reason == 'OK'


def test_icap_response_unexpected_keywords():
    with pytest.raises(ValueError) as excinfo:
        response.ICAPResponse(frob=2)
    assert excinfo.value.message.startswith('unexpected keyword arguments')


def test_icap_response_both_request_and_response_encapsulated():
    with pytest.raises(ValueError) as excinfo:
        response.ICAPResponse(http_request=1, http_response=1)
    expected_message = 'cannot encapsulate both request and response'
    assert excinfo.value.message.startswith(expected_message)


def test_bad_composition():
    reason = 'looks awful'
    err = response.BadComposition(reason=reason)
    assert err.status_code == 418
    assert err.reason == reason
    assert repr(err) == 'BadComposition({!r},)'.format(reason)


def test_service_not_found():
    err = response.ServiceNotFound()
    assert err.status_code == 404
    assert err.reason == 'ICAP Service not found'


def test_method_not_allowed():
    err = response.MethodNotAllowed()
    assert err.status_code == 405
    assert err.reason == 'Method not allowed for service'
