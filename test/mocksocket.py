from io import BytesIO


class MockWfile(BytesIO):

    value = None

    def close(self):
        self.value = self.getvalue()
        super(MockWfile, self).close()


class MockSocket(object):

    def __init__(self, request_bytes):
        self.rfile = BytesIO(request_bytes)
        self.wfile = None

    def makefile(self, mode, bufsize):
        if mode == 'rb':
            assert bufsize == -1
            return self.rfile
        elif mode == 'wb':
            assert bufsize == 0
            self.wfile = MockWfile()
            return self.wfile
        assert not mode
