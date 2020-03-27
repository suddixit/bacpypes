#!/usr/bin/env python

"""
This application is a special example of building a custom data structure
to be written to a proprietary property of a proprietary object.  Unlike the
other 'write property' sample applications, this one make no attempt to
translate keywords into object types and property identifiers, it only takes
integers.
"""

import sys

from bacpypes.debugging import bacpypes_debugging, ModuleLogger, xtob
from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.consolecmd import ConsoleCmd

from bacpypes.core import run, enable_sleeping
from bacpypes.iocb import IOCB

from bacpypes.pdu import Address
from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject

from bacpypes.primitivedata import TagList, OpeningTag, ClosingTag, ContextTag, ObjectIdentifier
from bacpypes.constructeddata import Any
from bacpypes.apdu import WritePropertyRequest, SimpleAckPDU

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# globals
this_application = None

#
#   WriteSomethingConsoleCmd
#

@bacpypes_debugging
class WriteSomethingConsoleCmd(ConsoleCmd):

    def do_write(self, args):
        """write <addr> <objid> <prop> [ <indx> ]"""
        args = args.split()
        if _debug: WriteSomethingConsoleCmd._debug("do_write %r", args)

        try:
            addr, obj_id, prop_id = args[:3]
            obj_id = ObjectIdentifier(obj_id).value
            prop_id = int(prop_id)

            # build a request
            request = WritePropertyRequest(
                objectIdentifier=obj_id,
                propertyIdentifier=prop_id,
                )
            request.pduDestination = Address(addr)

            if len(args) == 4:
                request.propertyArrayIndex = int(args[3])

            # build a custom datastructure
            tag_list = TagList([
                OpeningTag(1),
                ContextTag(0, xtob('9c40')),
                ContextTag(1, xtob('02')),
                ContextTag(2, xtob('02')),
                ClosingTag(1)
                ])
            if _debug: WriteSomethingConsoleCmd._debug("    - tag_list: %r", tag_list)

            # stuff the tag list into an Any
            request.propertyValue = Any()
            request.propertyValue.decode(tag_list)

            if _debug: WriteSomethingConsoleCmd._debug("    - request: %r", request)

            # make an IOCB
            iocb = IOCB(request)
            if _debug: WriteSomethingConsoleCmd._debug("    - iocb: %r", iocb)

            # give it to the application
            deferred(this_application.request_io, iocb)

            # wait for it to complete
            iocb.wait()

            # do something for success
            if iocb.ioResponse:
                # should be an ack
                if not isinstance(iocb.ioResponse, SimpleAckPDU):
                    if _debug: WriteSomethingConsoleCmd._debug("    - not an ack")
                    return

                sys.stdout.write("ack\n")

            # do something for error/reject/abort
            if iocb.ioError:
                sys.stdout.write(str(iocb.ioError) + '\n')

        except Exception as error:
            WriteSomethingConsoleCmd._exception("exception: %r", error)


#
#   __main__
#

def main():
    global this_application

    # parse the command line arguments
    args = ConfigArgumentParser(description=__doc__).parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # make a device object
    this_device = LocalDeviceObject(ini=args.ini)
    if _debug: _log.debug("    - this_device: %r", this_device)

    # make a simple application
    this_application = BIPSimpleApplication(this_device, args.ini.address)
    if _debug: _log.debug("    - this_application: %r", this_application)

    # make a console
    this_console = WriteSomethingConsoleCmd()
    if _debug: _log.debug("    - this_console: %r", this_console)

    # enable sleeping will help with threads
    enable_sleeping()

    _log.debug("running")

    run()

    _log.debug("fini")

if __name__ == "__main__":
    main()
