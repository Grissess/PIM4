'''
PIM4 -- Python Instant Messenger version 4
pump -- UPP Pump

Just a simple packet pump.
'''

import threading
import traceback

from upp.uppsocket import UPPSocket

class PacketPump(object):
    def __init__(self, sock):
        self.sock=UPPSocket.Wrap(sock)
        self.entry=lambda pkt, addr: None
        self.excentry=lambda pkt, addr, e: None
        self.thread=None
        self.started=False
    def SetEntry(self, entry):
        self.entry=entry
    def SetErrorEntry(self, excentry):
        self.excentry=excentry
    def Start(self):
        if not self.started:
            self.thread=threading.Thread(target=self._PumpThread, args=())
            self.thread.setDaemon(True)
            self.started=True
            self.thread.start()
    def Stop(self):
        self.started=False
    def _PumpThread(self):
        while self.started:
            try:
                pkt, addr=self.sock.RecvFrom()
            except Exception, e:
                print 'Oddly experienced an error in receiving from a non-connected socket'
                traceback.print_exc()
                print 'This is probably a socket crash on localhost. Continuing...'
            print repr(pkt)
            try:
                self.entry(pkt, addr)
            except Exception, e:
                traceback.print_exc()
                self.excentry(pkt, addr, e)
                print 'Pump is resiliently continuing...'