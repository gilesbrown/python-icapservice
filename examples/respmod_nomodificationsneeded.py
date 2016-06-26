""" An example ICAP service does no modifications. """

import logging
from icapservice import ICAPService, NoModificationsNeeded


class NoMod(ICAPService):

    abs_path = '/respmod'

    def RESPMOD(self, icap_request):
        return NoModificationsNeeded()


def main():
    logging.basicConfig(level=logging.INFO)
    NoMod().icap_handler_class().server().serve_forever()


if __name__ == '__main__':
    main()
