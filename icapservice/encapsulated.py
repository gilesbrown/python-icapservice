""" Parsing of the "Encapsulated" header.

See https://tools.ietf.org/html/rfc3507#section-4.4.1.
"""
from __future__ import print_function, unicode_literals
import re
from .response import BadComposition


encapsulated_list = re.compile('''
    \s*
    (?: (req-hdr) \s* = \s* (\d+) \s* , \s*)?
    (?: (res-hdr) \s* = \s* (\d+) \s* , \s*)?
    ((?:opt|req|res|null)-body) \s* = \s* (\d+)
    \s*
    $
''', re.VERBOSE)


def encapsulated_offsets(header):

    if not header:
        return []

    match = encapsulated_list.match(header)
    if not match:
        raise BadComposition(reason="cannot parse 'encapsulated' header")
    groups = match.groups()
    previous_offset = 0
    offsets = []
    for name, offset in zip(groups[::2], groups[1::2]):
        if name is None:
            continue
        offset = int(offset)
        if offset < previous_offset:
            raise BadComposition(reason="unordered offsets in 'encapsulated' header")
        offsets.append((name, offset))
        previous_offset = offset
    return offsets
