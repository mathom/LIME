#! /usr/bin/python
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

import sys
import struct
import wave
from StringIO import StringIO

# UI elements
from Tkinter import Tk
from tkFileDialog import askopenfilename

PREFIX = ''


class Chunk(object):
    def __init__(self, file, datacallback=None, debug=False):
        self.debug = debug
        self.datacallback = datacallback

        self.name = file.read(4)
        self.size = struct.unpack('<I', file.read(4))[0]

        if debug:
            print PREFIX + "\nRead: " + self.name + " size " + str(self.size)

        self.data = []

        self.children = []
        self.header = None
        if self.name == 'LIST':
            self.header = file.read(4)
            self.read_children(file, self.size)
        elif datacallback:
            datacallback(self, file)
        else:
            file.seek(self.size, 1)

    def read_children(self, file, stop):
        start = file.tell()
        global PREFIX
        PREFIX += "\t"
        while file.tell() < stop - start:
            self.children.append(Chunk(file, self.datacallback, self.debug))
        PREFIX = PREFIX[:-1]

    def __repr__(self):
        return "Chunk %s (size %d) (%d children)" % (
            self.name, self.size, len(self.children)
        )


class RIFF(object):
    def __init__(self, file, datacallback=None, debug=False):
        assert file.read(4) == 'RIFF'
        self.size = struct.unpack('<I', file.read(4))[0]  # total file size
        self.name = file.read(4)  # should be 'OMNI'
        assert self.name == 'OMNI'

        self.children = []
        while file.tell() < self.size + 4:
            self.children.append(Chunk(file, datacallback, debug))


def read_cstring(file):
    s = StringIO()
    c = ''
    while c != '\0':
        s.write(c)
        c = file.read(1)
    return s.getvalue()


def attacher(self, file):
    """Attaches blob data to the chunk in string form."""
    self.data = StringIO(file.read(self.size))


def dumper(self, file):
    global NUM
    blob = file.read(self.size)

    if blob.find(' WAV') != -1:
        listbegin = blob.find('LIST')
        idblock = StringIO(blob[:listbegin])

        idblock.seek(15, 1)
        name = read_cstring(idblock)

        blob = StringIO(blob[listbegin:])
        audiolist = Chunk(blob, attacher)

        try:
            process_audio(name, audiolist.children)
        # It ran into some non-audio data
        except Exception:
            print "Skipping...\n"


def process_header(chunk):
    data = chunk.data

    data.seek(18, 1)
    bitrate1 = struct.unpack('<H', data.read(2))[0]
    data.seek(2, 1)
    bitrate2 = struct.unpack('<H', data.read(2))[0]
    data.seek(2, 1)
    idk = struct.unpack('<H', data.read(2))[0]
    bits = struct.unpack('<H', data.read(2))[0]

    print "\nAudio format might be %dHz or %dHz, with %d bits\n" % (
        bitrate1, bitrate2, bits)

    return {'sampwidth': bits / 8, 'channels': 1, 'framerate': bitrate1}


def process_audio(name, chunks):
    junk = 0
    valid = 0

    head = chunks[0]
    wavinfo = process_header(head)

    print "\nWriting %s.wav\n" % name
    out = wave.open("%s.wav" % name, 'wb')
    out.setnchannels(wavinfo['channels'])
    out.setframerate(wavinfo['framerate'])
    out.setsampwidth(wavinfo['sampwidth'])

    for chunk in chunks[1:]:
        if chunk.name == 'MxCh':
            valid += 1
            chunk.data.seek(14, 0)
            out.writeframes(chunk.data.read())
        else:
            junk += 1

    out.close()
    print "stats: %d valid, %d junk" % (valid, junk)


def main():
    '''Simple GUI'''

    print "\nWelcome to LIME\n"

    # SI archive label
    fileformat = [("SI Archive", "*.SI")]

    # Draw (then withdraw) the root Tk window
    root = Tk()
    root.withdraw()

    # Overwrite root display settings
    root.overrideredirect(True)
    root.geometry('0x0+0+0')

    # Show window again, lift it so it can receive the focus
    # Otherwise, it is behind the console window
    root.deiconify()
    root.lift()
    root.focus_force()

    # Select the SI archive
    filename = askopenfilename(
        parent=root,
        title="Select a LEGO Island SI Archive",
        defaultextension=".SI",
        filetypes=fileformat
    )

    # The user clicked the cancel button
    if len(filename) == 0:

        # Give focus back to console window
        root.destroy()

        raw_input('''\nCould not find an SI Archive to extract!
Press Enter to close LIME.\n''')
        raise SystemExit

    # The user selected a patch
    else:

        # Give focus back to console window
        root.destroy()

        # Display intro text
        print "\nReading %s" % filename
        print "\n" + "-" * 40 + "\n"

        # Send archive to extractor
        RIFF(open(filename, 'rb'), dumper, debug=True)

if __name__ == "__main__":
    try:
        filename = sys.argv[1]

        # Send archive to extractor
        RIFF(open(filename, 'rb'), dumper, debug=True)

    # The command-line argument was not invoked, open file dialog
    except IndexError:
        main()
