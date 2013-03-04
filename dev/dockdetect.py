#!/usr/bin/env python

import struct
import signal
import sys

def sighandler(signum,frame):
    print('Exiting ...')
    sys.exit(0)

def notification():
    import pynotify
    pynotify.init('test')
    n = pynotify.Notification("Title", "body", "dialog-warning")
    n.set_urgency(pynotify.URGENCY_NORMAL)
    n.set_timeout(pynotify.EXPIRES_NEVER)
    #n.add_action("clicked","Button text", callback_function, None)
    n.show()
    #n.close()


if __name__=='__main__':
    
    eventformat = 'llHHi'
    device = '/dev/input/event5'

    signal.signal(signal.SIGINT,sighandler)
    signal.signal(signal.SIGTERM,sighandler)
    
    eventsize = struct.calcsize(eventformat)

    with open(device,'rb') as dev:
        while True:
            event = dev.read(eventsize)
            s,ns,type,code,value = struct.unpack(eventformat, event)
            print('{0} {1} {2} {3} {4}'.format(s,ns,type,code,value))
        
