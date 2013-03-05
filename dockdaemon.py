#!/usr/bin/python2

#
#   Copyright (C) 2013 Wainer Vandelli
#
#   This file is part of dockdetect.
#
#   dockdetect is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import daemon
from lockfile import pidlockfile
import os.path
import sys
import struct
from collections import namedtuple
import argparse
import contextlib

class InputEvent(namedtuple('_InputEvent', 'raw seconds nanoseconds type code value')):
    """
    Class providing input event decoding

    """
    _format = 'llHHi'
    size = struct.calcsize(_format)
    
    def __new__(cls, raw):
        decoded = struct.unpack(InputEvent._format, raw)
        return super(InputEvent,cls).__new__(cls,raw,*decoded)
        

def eventlistener(device):
    """
    Generator providing events from the input device as they became available
    
    """
    with open(device,'rb') as dev:
        while True:
            yield InputEvent(dev.read(InputEvent.size))
            

def main(device):

    listener = eventlistener(device)
    for event in listener:
        #if event.type == 5 and event.code == 5:
        #    pass
        print event.type

def parseargs():
    parser = argparse.ArgumentParser(description='Input event daemon.')
    parser.add_argument('-i','--no-daemon',action='store_true',dest='nodaemon')
    parser.add_argument('-c','--conf',action='store',required=True)
    return parser.parse_args()

def parseconf():
    pass

@contextlib.contextmanager
def nullcontext():
    """
    Null context manager

    """
    yield


if __name__ == '__main__':

    args = parseargs()

    conf = parseconf(args.conf)
    
    piddir = '/run'
    me = os.path.splitext(sys.argv[0])[0]
    device = '/dev/input/event4'


    if args.nodaemon:
        context = nullcontext()
    else:
        context = daemon.DaemonContext(
            pidfile=pidlockfile.PIDLockFile(os.path.join(piddir,me)),
            #stdout=open('/tmp/test.log','w')
            )

    with context:
        main(device)
