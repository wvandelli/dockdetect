#!/usr/bin/python2

import daemon
from lockfile import pidlockfile
import os.path
import sys
import struct
from collections import namedtuple

class InputEvent(namedtuple('_InputEvent', 'raw seconds nanoseconds type code value')):
    """
    Class providing input event decoding

    """
    _format = 'llHHi'
    size = struct.calcsize(_format)
    
    def __new__(cls, raw):
        decoded = struct.unpack(InputEvent._format, raw)
        return super(InputEvent,cls).__new__(cls,raw,*decoded)
        

def EventListener(device):
    """
    Generator providing events from the input device as they became available
    
    """
    with open(device,'rb') as dev:
        while True:
            yield InputEvent(dev.read(InputEvent.size))
            

def main(device):

    listener = EventListener(device)
    for event in listener:
        #if event.type == 5 and event.code == 5:
        #    pass
        print event.type


if __name__ == '__main__':

    piddir = '/run'
    me = os.path.splitext(sys.argv[0])[0]
    device = '/dev/input/event4'

    context = daemon.DaemonContext(
        pidfile=pidlockfile.PIDLockFile(os.path.join(piddir,me)),
        #stdout=open('/tmp/test.log','w')
    )

    with context:
        main(device)
