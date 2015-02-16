'''
upp -- Unified Packet Protocol
packet -- Packet

Defines the UPP Packet.

This is the most basic entity in UPP. It supports only its creation
(via __init__ with keyword arguments and a cmd) and turning into a
bytestring via __str__. __repr__ will print out the command, and a
list of arguments (useful for debugging). Finally, an UPP Packet can
be read back from a bytestring using .Parse(). Ultimately the codeflow
for sending and receiving a command looks like this:

SENDER:
p=Packet(cmd='UsefulCommand', arg='An argument', num=5)
sock.send(str(p)) #<- A connected UDP socket
...

RECEIVER:
data, peer=sock.recvfrom(BUF_SIZE)
p=Packet.Parse(data)

In theory, this should result in two congruent Packet objects; that
is, possessing the same attributes with equivalent values.

Serializeability is defined using the serialize module. All base types
can be serialized; this includes lists and tuples (which come out as
lists) as well as dicts (given that all items, keys, and/or values are
themselves serializeable). See there for more info.

Command/attribute name size limit is 256. Other limits are imposed by
serializers themselves.
'''

from const import *

import serialize

class Packet(object):
    def __init__(self, cmd, **kwargs):
        self.cmd=cmd[:256]
        self.attrs=kwargs.copy()
    def __str__(self):
        return chr(len(self.cmd))+self.cmd+serialize.Serialize(self.attrs)
    @classmethod
    def Parse(cls, s):
        cmdlen=ord(s[0])
        cmd=s[1:cmdlen+1]
        attrs=serialize.Deserialize(s[cmdlen+1:])
        assert isinstance(attrs, dict), 'Packet attrs was not a dict!'
        return cls(cmd, **attrs)
    def __repr__(self):
        return '<Packet cmd=%r attrs=%r>'%(self.cmd, self.attrs)
    def __getattr__(self, attr):
        return self.attrs[attr]
    def __setattr__(self, attr, val):
        if attr in ('cmd', 'attrs'):
            object.__setattr__(self, attr, val)
        else:
            self.attrs[attr]=val
