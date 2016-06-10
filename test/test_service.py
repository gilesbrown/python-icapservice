from icapservice import ICAPService


def test_istag():
    icap_service = ICAPService()
    istag = '123'
    icap_service.istag = istag
    assert icap_service.response_headers.get('istag') == istag
    assert icap_service.istag == istag


def test_new_http_response():
    icap_service = ICAPService()
    http_response = icap_service.new_http_response(403)
    assert http_response.protocol == 'HTTP/1.1'
    assert http_response.status_code == 403
    assert http_response.reason == 'Forbidden'


def test_new_http_response_other_protocol():
    icap_service = ICAPService()
    http_response = icap_service.new_http_response(200, 'HTTP/1.0')
    assert http_response.protocol == 'HTTP/1.0'
    assert http_response.status_code == 200
    assert http_response.reason == 'OK'
