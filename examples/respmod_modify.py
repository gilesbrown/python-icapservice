""" An example ICAP service that modifies response content.

Try visiting:

    $ export http_proxy=http://localhost:3128
    $ curl http://www.example.net/

And look for '<h1>Modifed Example Domain</h1>'

"""

import logging
from icapservice import ICAPService, OK


class Modify(ICAPService):

    abs_path = '/respmod'

    def RESPMOD(self, icap_request):
        http_response, chunks = icap_request.modify_http_response()
        return OK(http_response=http_response, chunks=self.modify_chunks(chunks))

    def modify_chunks(self, chunks):
        before  = 'Example Domain'
        after = before.replace('Example', 'Modified Example')
        for chunk in chunks:
            if before in chunk:
                chunk = chunk.replace(before, after)
            yield chunk


def main():
    logging.basicConfig(level=logging.INFO)
    Modify().icap_handler_class().server().serve_forever()


if __name__ == '__main__':
    main()
