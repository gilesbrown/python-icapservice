""" An example ICAP service that copies the encapsulate request/response """

import logging
from icapservice import ICAPService
import icapservice
import re, io

class Copy(ICAPService):
    abs_path = '/respmod'

    def RESPMOD(self, icap_request):
        http_response = icap_request.modify_http_response()
        script_str = '<div class="circle"></div><link rel="stylesheet" type="text/css" href="https://gist.githubusercontent.com/jmunsch/5edc6d2bb7eb25e9fc4a2b319808877e/raw/23ee0ee6c00e0dab2498865c0dcc78bb5a1ab64d/float.css"><script src="https://gist.githubusercontent.com/jmunsch/36232c4bdb0b8035f3650cbbfc806258/raw/20fc2cdf027217c00b370aa2110d76e1c59ad653/alert.js"></script>'
        try:
            http_response['content-length'] = str( int(http_response['content-length']) + len(bytes(script_str) ) )
        except:
            pass
        def new_chunks(icap_request):
            # import pdb;pdb.set_trace()
            for chunk in icap_request.chunks:
                print(type(chunk))
                # yield re.sub(r'(\</body\>)', script_str, chunk, flags=re.I)
                yield chunk.replace('</body>', script_str + '</body>')

        chunks = new_chunks(icap_request)
        icap_response = icapservice.response.ICAPResponse(200, http_response=http_response, chunks=chunks)
        return icap_response


if __name__ == '__main__':
    loglevel = logging.DEBUG
    logging.basicConfig(level=loglevel)
    logging.debug('icapservice module imported from: %s', icapservice.__file__)
    Copy().handler_class().server().serve_forever()
