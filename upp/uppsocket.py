'''
upp -- Unified Packet Protocol
uppsocket -- UPP Sockets

Defines basic extension sockets.

The UPPSocket class can be used to wrap a normal UDP socket and
provide some extensible behavior. (The extended names follow the
normal CamelCase convention, but the other methods are passed through
the wrapper courtesy __getattr__.)

You can also use a PollGroup to efficiently return a list of UPPSockets
(or, even regular sockets for that matter) that have pending data.
'''

import select

from const import *
from packet import Packet

class UPPSocket(object):
    def __init__(self, sock):
        self.sock=sock
    @classmethod
    def Wrap(cls, inst):
        if not isinstance(inst, cls):
            return cls(inst)
        return inst
    def SendTo(self, addr, packet):
        self.sock.sendto(str(packet), addr)
    def RecvFrom(self, bufsize=BUF_SIZE):
        data, addr=self.sock.recvfrom(bufsize)
        return Packet.Parse(data), addr
    def Poll(self):
        return bool(select.select([self], [], [], 0)[0])
    def __getattr__(self, name):
        return getattr(self.sock, name)

class PollGroup(object):
    def __init__(self, socks=()):
        self.socks=set(socks)
    def AddSocket(self, sock):
        self.socks.add(sock)
    def RemoveSocket(self, sock):
        self.socks.discard(sock)
    def Poll(self):
        return select.select(list(self.socks), [], [], 0)[0]
