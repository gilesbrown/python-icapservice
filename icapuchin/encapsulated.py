""" Parsing of the "Encapsulated" header.

See https://tools.ietf.org/html/rfc3507#section-4.4.1.
"""
from __future__ import print_function, unicode_literals
import re


class EncapsulationError(Exception):
    """ The encapsulation in the request is wrong """


encapsulated_list = re.compile('''
    \s*
    (?: (req-hdr) \s* = \s* (\d+) \s* , \s*)?
    (?: (res-hdr) \s* = \s* (\d+) \s* , \s*)?
    ((?:opt|req|res|null)-body) \s* = \s* (\d+)
    \s*
    $
''', re.VERBOSE)


def encapsulated_offsets(request):

    header = request.get('encapsulated')
    if header is None:
        return []

    match = encapsulated_list.match(header)
    if not match:
        raise EncapsulationError("no match '%r'" % header)
    groups = match.groups()
    previous_offset = 0
    offsets = []
    for name, offset in zip(groups[::2], groups[1::2]):
        if name is None:
            continue
        offset = int(offset)
        if offset < previous_offset:
            raise EncapsulationError("unordered offsets '%s'" % header)
        offsets.append((name, offset))
        previous_offset = offset
    return offsets
