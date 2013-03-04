#!/usr/bin/python2

import daemon
import time
#import signal
#import sys
from lockfile import pidlockfile
from logging.handlers import SysLogHandler
import logging

#start-stop-daemon --start --pidfile /var/run/test.pid --exec ~vandelli/pydaemon.py

#def sighandler(signum,frame):
#    print('Exiting ...')
#    sys.exit(0)

def main():

    logger = logging.getLogger()
    logger.addHandler(SysLogHandler('/dev/log'))
    
    while True:
        print "I'm alive"
        logging.warn("I'm alive")
        time.sleep(10)



if __name__ == '__main__':

    context = daemon.DaemonContext(
        pidfile=pidlockfile.PIDLockFile('/var/run/test.pid'),
        stdout=open('/tmp/test.log','w')
    )

    with context:
        main()
