""" HTTP content decoding. """

from __future__ import unicode_literals
import zlib


def decode_identity(chunks):

    for chunk in chunks:
        yield chunk


def decode_deflate(chunks, z=None):

    if z is None:
        z = zlib.decompressobj()
        retry = True
    else:
        retry = False

    for chunk in chunks:

        compressed = (z.unconsumed_tail + chunk)
        try:
            decompressed = z.decompress(compressed)
        except zlib.error:
            if not retry:
                raise
            z = zlib.decompressobj(-zlib.MAX_WBITS)
            retry = False
            decompressed = z.decompress(compressed)

        if decompressed:
            yield decompressed

    yield z.flush()


def decode_gzip(chunks):
    return decode_deflate(chunks, zlib.decompressobj(16 + zlib.MAX_WBITS))


decoders = {
    'deflate': decode_deflate,
    'gzip': decode_gzip,
    'identity': decode_identity,
}
