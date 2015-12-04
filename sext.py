'''
PIM4 -- Python Instant Messenger version 4
sext -- Server Extensions

Implements extensions on the server. These are intended to be atomic, independent,
and completely interoperable.

LoadExtensions returns a list of SExtension classes which can be instantiated.

Note that in certain situations (PreRecvPacket especially), cli may be None (if the
client is not Synced).

SExtensions must return True from UnknownPacket (or a dispatch derivative) to
prevent the default error reply from the server. Upon returning True, no other
SExtensions receive an UnknownPacket.

SExtensions may return True from PreRecvPacket and PreDispatchPacket to prevent their
default actions as well.
'''

import os

class SExtension(object):
    @property
    def CANON_NAME(self):
        raise NotImplementedError('SExtension must define a string .CANON_NAME')
    @property
    def VERSION(self):
        raise NotImplementedError('SExtension must define an integer .VERSION')
    def __init__(self, server):
        self.server=server
    def PreRecvPacket(self, pkt, addr):
        pass
    def PreDispatchPacket(self, cli, pkt):
        pass
    def UnknownPacket(self, cli, pkt):
        return getattr(self, 'cmd_'+pkt.cmd, self.UnimplementedPacket)(cli, pkt)
    def UnimplementedPacket(self, cli, pkt):
        pass #This is generally always a good idea to leave alone.

def LoadExtensions():
    mods=[]
    for i in os.listdir('.'):
        if i.startswith('sext_') and (i.endswith('.py') or i.endswith('.pyc')):
            mod=__import__(i.partition('.')[0])
            if mod not in mods:
                mods.append(mod)
    return [mod.Extension for mod in mods]
