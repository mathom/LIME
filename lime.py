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

import os
import string
import struct
import sys


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


def read_cstr(handle):
    s =''
    c = handle.read(1)
    while c != '\0':
        s += c
        c = handle.read(1)
    return s


def assert_empty(data, crash=True):
    for c in data:
        if c != '\0':
            hexdump(data)
            if crash:
                raise AssertionError


def assert_equals(a, b):
    if a != b:
        hexdump(a)
        print 'is not equal to'
        hexdump(b)
        raise AssertionError


TYPES = {
    0x07: 'list_head',
}

FLAG_TAGGED = 0x20


def read_object(handle, seek, level=0, callback=None):
    handle.seek(seek)

    fields = dict(
    )

    chunk_content = struct.unpack('h', handle.read(2))[0]
    idx = 2

    group = read_cstr(handle)
    assert_empty(handle.read(4))
    idx += 4

    label = read_cstr(handle)

    content_label = TYPES.get(chunk_content, 'unknown:{0}'.format(chunk_content))
    print '{0} {1} "{2}" "{3}"'.format('->'*level, content_label, group, label)

    if TYPES.get(chunk_content) == 'list_head':
        alpha, beta = struct.unpack('ii', handle.read(8))

        assert_empty(handle.read(8))

        gamma = struct.unpack('i', handle.read(4))[0]

        assert_empty(handle.read(46), crash=False) #TODO

        assert_equals(handle.read(16), '\xf0\x3f' + '\0'*14)

        assert_equals(handle.read(10), '\xf0\x3f' + '\0'*8)

        print '{0} alpha = {1:x} {1:b}\n{0} beta = {2:x} {2:b}'.format('  '*level, alpha, beta)
        if beta & FLAG_TAGGED:
            count = struct.unpack('h', handle.read(2))[0]
            if count != 0:
                tags = read_cstr(handle)
                print '  '*level, 'tags', tags

        print '{0} internal chunk at {1:x}'.format('  '*level, handle.tell())
        read_chunk(handle, handle.tell(), level=level+1, callback=callback)

    return fields


def read_chunk(handle, seek=0, level=0, callback=None):
    handle.seek(seek)

    chunk_id = handle.read(4)
    chunk_length = struct.unpack('i', handle.read(4))[0]
    chunk_type = None

    if chunk_id in ('RIFF', 'LIST'):
        chunk_type = handle.read(4)
        chunk_length -= 4

    data_start = handle.tell()

    print '->'*level, chunk_id, '({0})'.format(chunk_type) if chunk_type else ''
    print '  '*level, 'at {0:x} <{1:x}>'.format(seek, chunk_length)

    if chunk_type or chunk_id == 'MxSt':
        data = []
        handle_seek = data_start

        if chunk_type == 'MxCh':
            count = struct.unpack('i', handle.read(4))[0]
            handle_seek += 4
            print '{0} mxch chunk count {1}'.format('  '*level, count)

        while handle_seek - data_start < chunk_length:
            print '* '*level, '{0:x} < {1:x}'.format(handle_seek - data_start, chunk_length)
            subchunk = read_chunk(handle, handle_seek, level+1)
            handle_seek += subchunk['read']
            # data.append(subchunk[3])
        if chunk_id == 'LIST':
            pass
            # print 'list', len(data)
            #hexdump(data[0][0:100])
    # else:
        # data = handle.read(chunk_length)

    if chunk_id == 'MxOb':
        # print chunk_id, data_start
        read_object(handle=handle, seek=data_start, level=level, callback=callback)
        #hexdump(data[idx:80+idx])

    if data_start == 3744:
        print '!'*100

    handle.seek(data_start + chunk_length)

    if chunk_length % 2 != 0: # eat pad byte
        handle.read(1)

    return dict(
        id=chunk_id,
        length=chunk_length,
        type=chunk_type,
        # data=data,
        read=handle.tell() - seek
    )


def write_file(chunk_id, title, content):
    print chunk_id, title


if __name__=='__main__':
    try: 
        filename = sys.argv[1]
    except:
        print "Usage: %s file.si" % sys.argv[0]
        raise SystemExit

    print "Reading %s" % filename
    print "-"*40

    in_file = open(filename, 'rb')

    dirname = os.path.splitext(filename)[0]
    if not os.path.exists(dirname):
        os.mkdir(dirname)

    os.chdir(dirname)

    read_chunk(in_file, callback=write_file)
