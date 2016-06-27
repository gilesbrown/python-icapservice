""" An example ICAP service that copies the encapsulated response. """

import logging
from icapservice import ICAPService, OK

class Copy(ICAPService):

    abs_path = '/respmod'

    def RESPMOD(self, icap_request):
        http_response, chunks = icap_request.modify_http_response(decode=False)
        return OK(http_response=http_response, chunks=chunks)


def main():
    logging.basicConfig(level=logging.INFO)
    Copy().icap_handler_class().server().serve_forever()


if __name__ == '__main__':
    main()
