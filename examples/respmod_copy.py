""" An example ICAP service that copies the encapsulate request/response """

import logging
from icapservice import ICAPService


class Copy(ICAPService):

    def RESPMOD(self, icap_request):
        return icap_request.copy(icap_request)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    Copy().handler_class().server().serve_forever()
