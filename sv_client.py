'''
PIM4 -- Python Instant Messenger version 4
sv_client -- Defines server representation of a client

Defines the server's representation of a client.

We're expecting a UPPSocket here.
'''

from modes import Modes, MODE

from upp.packet import Packet
from upp.uppsocket import UPPSocket

class Client(object):
    def __init__(self, sock, peer, nick):
        self.sock=UPPSocket.Wrap(sock)
        self.peer=peer
        self.nick=nick
        self.modes=Modes()
    def __getattr__(self, attr):
        return getattr(self.sock, attr)
    def Msg(self, source, target, body, sonic=False):
        self.SendTo(self.peer, Packet('Msg', source=source, target=target, body=body, sonic=sonic))
    def Packet(self, cmd, **kwargs):
        print 'CLI: Sending packet to', self.peer
        self.SendTo(self.peer, Packet(cmd, **kwargs))
    def Error(self, code, desc):
        print 'CLI: Sending error to', self.peer
        self.SendTo(self.peer, Packet('Error', code=code, desc=desc))
    def IsSop(self):
        return self.modes.Check(MODE.SOP) and not self.modes.Check(MODE.PRETENDING)