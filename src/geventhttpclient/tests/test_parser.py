from geventhttpclient.response import HTTPResponse
from geventhttpclient._parser import HTTPParseError
from cStringIO import StringIO
import pytest

RESPONSE = 'HTTP/1.1 301 Moved Permanently\r\nLocation: http://www.google.fr/\r\nContent-Type: text/html; charset=UTF-8\r\nDate: Thu, 13 Oct 2011 15:03:12 GMT\r\nExpires: Sat, 12 Nov 2011 15:03:12 GMT\r\nCache-Control: public, max-age=2592000\r\nServer: gws\r\nContent-Length: 218\r\nX-XSS-Protection: 1; mode=block\r\n\r\n<HTML><HEAD><meta http-equiv="content-type" content="text/html;charset=utf-8">\n<TITLE>301 Moved</TITLE></HEAD><BODY>\n<H1>301 Moved</H1>\nThe document has moved\n<A HREF="http://www.google.fr/">here</A>.\r\n</BODY></HTML>\r\n'

def test_refcount():
    import gc
    gc.set_debug(gc.DEBUG_LEAK)
    try:
        parser = HTTPResponse()
        assert parser.feed(RESPONSE), len(RESPONSE)
        del parser
    finally:
        gc.set_debug(0)

def test_parse():
    parser = HTTPResponse()
    assert parser.feed(RESPONSE), len(RESPONSE)
    assert parser.message_begun
    assert parser.headers_complete
    assert parser.message_complete

def test_parse_small_chunks():
    parser = HTTPResponse()
    parser.feed(RESPONSE)
    response = StringIO(RESPONSE)
    while not parser.message_complete:
        data = response.read(10)
        parser.feed(data)

    assert parser.message_begun
    assert parser.headers_complete
    assert parser.message_complete
    assert parser.should_keep_alive()
    assert parser.status_code == 301
    assert sorted(parser.items()) == [
        ('cache-control', 'public, max-age=2592000'),
        ('content-length', '218'),
        ('content-type', 'text/html; charset=UTF-8'),
        ('date', 'Thu, 13 Oct 2011 15:03:12 GMT'),
        ('expires', 'Sat, 12 Nov 2011 15:03:12 GMT'),
        ('location', 'http://www.google.fr/'),
        ('server', 'gws'),
        ('x-xss-protection', '1; mode=block'),
    ]

def test_parse_error():
    response =  HTTPResponse()
    try:
        response.feed("HTTP/1.1 asdf\r\n\r\n")
        response.feed("")
        assert response.status_code, 0
        assert response.message_begun
    except HTTPParseError as e:
        assert 'invalid HTTP status code' in str(e)
    else:
        assert False, "should have raised"

def test_incomplete_response():
    response = HTTPResponse()
    response.feed("""HTTP/1.1 200 Ok\r\nContent-Length:10\r\n\r\n1""")
    with pytest.raises(HTTPParseError):
        response.feed("")
    assert response.should_keep_alive() == False

def test_response_too_long():
    response = HTTPResponse()
    data = """HTTP/1.1 200 Ok\r\nContent-Length:1\r\n\r\ntoolong"""
    with pytest.raises(HTTPParseError):
        response.feed(data)


STATUS_CODES = {
  100 : 'Continue',
  101 : 'Switching Protocols',
  200 : 'OK',
  201 : 'Created',
  202 : 'Accepted',
  203 : 'Non-Authoritative Information',
  204 : 'No Content',
  205 : 'Reset Content',
  206 : 'Partial Content',
  300 : 'Multiple Choices',
  301 : 'Moved Permanently',
  302 : 'Moved Temporarily',
  303 : 'See Other',
  304 : 'Not Modified',
  305 : 'Use Proxy',
  400 : 'Bad Request',
  401 : 'Unauthorized',
  402 : 'Payment Required',
  403 : 'Forbidden',
  404 : 'Not Found',
  405 : 'Method Not Allowed',
  406 : 'Not Acceptable',
  407 : 'Proxy Authentication Required',
  408 : 'Request Time-out',
  409 : 'Conflict',
  410 : 'Gone',
  411 : 'Length Required',
  412 : 'Precondition Failed',
  413 : 'Request Entity Too Large',
  414 : 'Request-URI Too Large',
  415 : 'Unsupported Media Type',
  500 : 'Internal Server Error',
  501 : 'Not Implemented',
  502 : 'Bad Gateway',
  503 : 'Service Unavailable',
  504 : 'Gateway Time-out',
  505 : 'HTTP Version not supported'
}
