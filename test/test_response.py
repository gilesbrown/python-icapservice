import pytest
from icapuchin.response import ICAPResponse


def test_icap_response():
    ICAPResponse()


def test_icap_response_unexpected_keywords():
    with pytest.raises(ValueError) as excinfo:
        ICAPResponse(frob=2)
    assert excinfo.value.message.startswith('unexpected keyword arguments')


def test_icap_response_both_request_and_response_encapsulated():
    with pytest.raises(ValueError) as excinfo:
        ICAPResponse(encapsulated_request=1, encapsulated_response=1)
    assert excinfo.value.message.startswith('cannot encapsulate both request and response')
