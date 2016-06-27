""" An ICAP response copy service using a gevent StreamServer. """

import logging
from respmod_copy import Copy


def main():
    import gevent.server
    logging.basicConfig(level=logging.INFO)
    Copy().icap_handler_class().server(gevent.server.StreamServer).serve_forever()


if __name__ == '__main__':
    main()
