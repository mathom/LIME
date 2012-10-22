# LIME Copyright (C) 2011 Matthew Thompson, Nick Thompson
#
# This file is part of LIME.
#
# LIME is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# LIME is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with LIME.  If not, see <http://www.gnu.org/licenses/>.

import sys, struct, string


def hexdump(line):
    def format_char(c):
        if c in string.whitespace:
            return '_'
        elif c not in string.printable:
            return '.'
        else:
            return c
    print " ".join(format_char(c) for c in line)
    print "".join('%02x' % ord(c) for c in line)


def read_chunk(handle, level=0):
    chunk_id = handle.read(4)
    chunk_length = struct.unpack('i', handle.read(4))[0]
    chunk_type = None

    if chunk_id in ('RIFF', 'LIST'):
        chunk_type = handle.read(4)
        chunk_length -= 4

    data_start = handle.tell()

    print '    '*level, chunk_id, '({})'.format(chunk_type) if chunk_type else ''

    if chunk_type or chunk_id == 'MxSt':
        data = []
        while handle.tell() - data_start < chunk_length:
            subchunk = read_chunk(handle, level+1)
            data.append(subchunk[3])
    else:
        data = handle.read(chunk_length)

    if chunk_id == 'MxOb':
        idx = 2
        group = None

        def read_cstr(d, i):
            start = i
            while d[i] != '\0':
                i += 1
            return d[start:i], i

        if data[idx] != '\0': # there is a group
            group, idx = read_cstr(data, idx)
            print group,

        idx += 5
        label, idx = read_cstr(data, idx)

        print label
        hexdump(data[idx:70+idx])

    if chunk_id == 'MxCh':
        hexdump(data[:70])

    if chunk_length % 2 != 0: # eat pad byte
        handle.read(1)

    return chunk_id, chunk_length, chunk_type, data


if __name__=='__main__':
    try: 
        filename = sys.argv[1]
    except:
        print "Usage: %s file.si" % sys.argv[0]
        raise SystemExit

    print "Reading %s" % filename
    print "-"*40

    read_chunk(open(filename, 'rb'))
