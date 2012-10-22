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

def read_chunk(handle, level=0):
    chunk_id = handle.read(4)
    chunk_length = struct.unpack('i', handle.read(4))[0]
    chunk_type = None

    if chunk_id in ('RIFF', 'LIST'):
        chunk_type = handle.read(4)
        chunk_length -= 4

    data_start = handle.tell()

    # print '    '*level, chunk_id, chunk_length, chunk_type

    if chunk_type:
        data = []
        while handle.tell() - data_start < chunk_length:
            subchunk = read_chunk(handle, level+1)
            data.append(subchunk[3])
    else:
        data = handle.read(chunk_length)

    if chunk_id == 'MxSt':
        prev = data[:min(100, chunk_length)]
        name = prev[:4]
        length = struct.unpack('i', prev[4:8])[0]
        # data = data[8:]
        print name, length
        # print 'num of Mx', data.count('MxOb')
        line = data[:70]
        def format_char(c):
            if c in string.whitespace:
                return ' '
            elif c not in string.printable:
                return '.'
            else:
                return c
        print " ".join(format_char(c) for c in line)
        print "".join('%02x' % ord(c) for c in line)


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