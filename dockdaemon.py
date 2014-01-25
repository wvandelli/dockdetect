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
import ConfigParser
from glob import iglob
import subprocess
import os
import fcntl
import logging
from logging.handlers import SysLogHandler


IOC_NRBITS = 8L
IOC_TYPEBITS = 8L
IOC_SIZEBITS = 14L
IOC_DIRBITS = 2L

IOC_NRSHIFT = 0L
IOC_TYPESHIFT = IOC_NRSHIFT+IOC_NRBITS
IOC_SIZESHIFT = IOC_TYPESHIFT+IOC_TYPEBITS
IOC_DIRSHIFT = IOC_SIZESHIFT+IOC_SIZEBITS

IOC_READ = 2L


def EVIOCGNAME(length):
    return (IOC_READ << IOC_DIRSHIFT) \
        | (length << IOC_SIZESHIFT) \
        | (0x45 << IOC_TYPESHIFT) \
        | (0x06 << IOC_NRSHIFT)


def fetchname(device):
    """
    Return the device name for the provided device

    """
    try:
        buffer = "\0"*512
        fd = os.open(device, os.O_RDWR | os.O_NONBLOCK)
        name = fcntl.ioctl(fd, EVIOCGNAME(256), buffer)
        name = name[:name.find("\0")]
    except (IOError, OSError) as err:
        msg = "ioctl(EVIOCGNAME) for '{}' failed: {}".format(device, str(err))
        logging.getLogger().error(msg)
        name = None
    finally:
        os.close(fd)

    return name


def finddevice(name):
    """
    Loop over input devices and returns the first device whose name matches
    the provide name, None otherwise.

    """
    devices = (dev for dev in iglob('/dev/input/*')
               if not os.path.isdir(dev))

    for dev in devices:
        if fetchname(dev) == name:
            return dev

    return None


class InputEvent(namedtuple('_InputEvent',
                            'raw seconds nanoseconds type code value')):
    """
    Class providing input event decoding

    """
    _format = 'llHHi'
    size = struct.calcsize(_format)

    def __new__(cls, raw):
        decoded = struct.unpack(InputEvent._format, raw)
        return super(InputEvent, cls).__new__(cls, raw, *decoded)


def eventlistener(device):
    """
    Generator providing events from the input device as they became available

    """

    with open(device, 'rb') as dev:
        while True:
            yield InputEvent(dev.read(InputEvent.size))


def executetargets(dir, event):
    """
    Discovers target scripts and executes them (if they are executable)

    """

    targets = iglob(os.path.join(dir, '*'))
    targets = (t for t in targets if os.access(t, os.X_OK))
    targets = sorted(targets)
    for t in targets:
        try:
            logging.getLogger().info("Executing target: {}".format(t))
            _ = subprocess.check_output([t, "{}".format(event.value)],
                                        stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            logger = logging.getLogger()
            msg = "Target '{}' failed with exit code {}"
            msg.format(t, e.returncode)
            logger.warn(msg)
            logger.debug("Target '{}' failed. Output:\n{}".format(t, e.output))


def main(configuration):
    """
    Main iteration loop operating on incoming events

    """

    handler = SysLogHandler('/dev/log', facility=SysLogHandler.LOG_DAEMON)

    logformat = 'dockdetect[%(process)d]: %(message)s'
    handler.setFormatter(logging.Formatter(logformat))

    logger = logging.getLogger()
    logger.addHandler(handler)

    try:
        device = configuration['device']
    except KeyError:
        device = finddevice(configuration['devicename'])

    listener = eventlistener(device)
    logger.warn("started")
    for event in listener:
        if event.type == int(configuration['eventtype']) and \
           event.code == int(configuration['eventcode']):
            logger.warn("event detected. Value {}".format(event.value))
            executetargets(configuration['scriptdir'], event)


def parseargs():
    """
    Parse command line arguments

    """

    parser = argparse.ArgumentParser(description='Input event daemon.')
    parser.add_argument('-i', '--no-daemon',
                        action='store_true', dest='nodaemon')
    parser.add_argument('-c', '--conffile', action='store', required=True)
    parser.add_argument('-p', '--pidfile', action='store', required=True)
    return parser.parse_args()


def parseconf(conffile):
    """
    Parse configuration file

    """

    config = ConfigParser.SafeConfigParser()

    with open(conffile, 'rb') as configfile:
        config.readfp(configfile)

    return dict(config.items('Main'))


@contextlib.contextmanager
def nullcontext():
    """
    Null context manager

    """
    yield


if __name__ == '__main__':

    args = parseargs()

    conf = parseconf(args.conffile)

    me = os.path.splitext(os.path.basename(sys.argv[0])[0])[0]

    if args.nodaemon:
        context = nullcontext()
    else:
        context = daemon.DaemonContext(
            pidfile=pidlockfile.PIDLockFile(args.pidfile),
            )

    with context:
        main(conf)
