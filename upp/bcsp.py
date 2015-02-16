'''
upp -- Unified Packet Protocol
bcsp -- Binary Compressed Streaming Protocol

Defines Binary Compressed Streaming Protocol.

BCSP throws out the rules of UPP (for the most part) and defines its
own, somewhat inflexible binary-based protocol. Because the protocol
is binary, it is FAST. In order to increase throughput even further,
the payload is compressed with bzip2. Both of these go against the
general idea of data representation in UPP: the Packet is not a dict
in arbitrary order, and there is no command indicator, just a
bitfield.

Unlike RSP, we take a more TCP-style approach. RSP uses interleaving
Acks to ensure that only one packet is fresh on the line at any time,
which guarantees order. This is fine for hosts which have equal
bandwidth, but requires an Ack for every single chunk. Furthermore,
data cannot be pushed until the rather short Ack is produced.

Like RSP, we used session identifiers. Unlike RSP, we strictly enforce
that these session identifiers are integers, for obvious reasons. BCSP
also uses service identifiers, but, again, these are numeric.

BCSP is duplex, unlike RSP, and it takes out all the stops; it is UPP's
rebellious nephew. Again, all BCSP connections can go through a single
shared UDP socket, or, for that matter, any socket which supports a
datagram-like protocol (like IP or even Ethernet). BCSP is designed
for throughput, and its compression scheme may require some processing
power, so expect to spend a little time pumping data from both ends.

BCSP may seem to be a little odd in its sending protocol; it expects a
seekable file-like object. The reason for this is that the BCSP receiver
is expecting that the peer can seek to any location in its data stream.
The two major ways of interfacing a connection this are by using the
method .SetFile() to set a new file-like object (AFTER the we know the
transfer is done, otherwise data will be lost and the peer will receive
SEEKLIM errors from its outstanding ACKs) or .Push() to push some data
onto the file already there; if the file already there is not a StringIO,
it will be read into a read-only StringIO, and then the data pushed (so
it doesn't interfere with, e.g., open files).

BCSP's protocol is too complex to describe here, easily. One day, I'll
document it in some RFC-style document.
'''

import struct
import bz2
import zlib
import cStringIO

from const import *

class BCSPPacket(object):
    FUNC=struct.Struct('LLBBL') #The header structure
    def __init__(self, sid=0, service=0, op=BCSP.SYNC, err=BCSPERR.OK, sptr=0, data='', validate=False, fix=False):
        self.sid=sid
        self.service=service
        self.op=op
        self.err=err
        self.sptr=sptr
        self.data=data
        if validate:
            self.Validate(fix)
    @classmethod
    def Parse(cls, s):
        sid, service, op, er, sptr=cls.FUNC.unpack(s[:cls.FUNC.size])
        return cls(sid, service, op, err, sptr, s[cls.FUNC.size:])
    def Validate(self, fix=True):
        if self.err!=BCSPERR.OK:
            if self.op!=BCSP.NOP:
                if fix:
                    self.op=BCSP.NOP
                else:
                    raise ValueError('Error packet should have NOP operation')
        if self.op==BCSP.CMP:
            if len(self.data)>2:
                if fix:
                    self.data=self.data[:2]
                else:
                    raise ValueError('CMP packet must have two bytes of data (comp mode, level)')
            elif len(self.data)<2:
                raise ValueError('CMP packet must have two bytes of data (comp mode, level)')
            if ord(self.data[1])>9:
                if fix:
                    self.data=self.data[0]+chr(9)
                else:
                    raise ValueError('CMP level must be 1-9')
            elif ord(self.data[1])==0:
                if fix:
                    self.data=self.data[0]+chr(1)
                else:
                    raise ValueError('CMP level must be 1-9')
    def __str__(self):
        return self.FUNC.pack(self.sid,
                              self.service,
                              self.op,
                              self.err,
                              self.sptr)+self.data
    def __repr__(self):
        return '<BCSPPacket sid=%r service=%r op=%r err=%r sptr=%r>'%(self.sid,
                                                                      self.service,
                                                                      self.op,
                                                                      self.err,
                                                                      self.sptr)

class BCSPTransponder(object):
    SID=0
    def __init__(self, sock, service, peer=None, mode=BCSPCMP.NONE, desmode=BCSPCMP.BZIP2, deslead=BCSP_DESLEAD):
        self.sock=sock
        self.peer=peer
        self.sid=None
        self.service=service
        self.mode=mode
        self.desmode=desmode
        self.state=BCSPS.NOTCON
        self.file=None
        self.origin=0
        self.lastack=0
        self.lastsent=0
        self.deslead=deslead
        self.buffer=''
        self.chunk=BCSP_CHUNK
    def Connect(self, peer, sid=None, kick=True):
        if self.state!=BCSPS.NOTCON:
            if kick:
                self.sock.sendto(str(BCSPPacket(self.sid, self.service, BCSP.NOP, BCSPERR.ABORT)), self.peer)
                self.peer=None
            else:
                raise RuntimeError('Transponder is already connected')
        if sid is None:
            self.sid=self.SID
            self.SID+=1
        else:
            self.sid=sid
        self.peer=peer
        self.sock.sendto(str(BCSPPacket(self.sid, self.service, BCSP.SYNC)), peer)
        #If they SYNC back, we'll set self.state
    def Disconnect(self):
        if self.state==BCSPS.NOTCON:
            raise RuntimeError('Transponder is not connected')
        self.sock.sendto(str(BCSPPacket(self.sid, self.service, BCSP.FIN)), self.peer)
        #We'll wait for the packet again, but we must set the state here
        self.state=BCSPS.CLOSING
    def Kick(self):
        if self.state==BCSPS.NOTCON:
            raise RuntimeError('Transponder is not connected')
        self.sock.sendto(str(BCSPPacket(self.sid, self.service, BCSP.NOP, BCSPERR.ABORT)))
        self.state=BCSPS.NOTCON
        self.peer=None
        self.origin=0
        self.lastack=0
    def SetFile(self, f):
        if self.state in (BCSPS.NOTCON, BCSPS.CLOSING):
            #Hey, we're not connected, we don't have to deal with this origin crap
            self.origin=0
            self.file=f
            self.lastsent=0
            self.lastack=0
        else:
            #We have to live-switch the file. It could get ugly; the last one will be interrupted.
            self.origin=self.lastsent
            self.sock.sendto(str(BCSPPacket(self.sid, self.service, BCSP.NO, sptr=self.origin)), self.peer)
    def Push(self, data):
        if isinstance(self.file, cStringIO.OutputType):
            newf=cStringIO.StringIO(self.file.getvalue()+data)
        else:
            self.file.seek(0)
            newf=cStringIO.StringIO(self.file.read()+data)
        self.file=newf #Which should have the same information in the same position...
    def Pump(self):
        self.sock.settimeout(const.BCSP_WAITTIME)
        try:
            while True:
                data, addr=self.sock.recvfrom(BUF_SIZE)
                pkt=BSCPPacket.Parse(data)
                if pkt.op==BCSP.TMIT:
                    self.buffer+=pkt.data
                    self.sock.sendto(str(BCSPPacket(self.sid, self.service, BCSP.ACK, sptr=pkt.sptr)), self.peer)
                elif pkt.op==BCSP.SYNC:
                    if self.state==BCSPS.NOTCON:
                        
        except socket.timeout:
            #Possibly send some packets
            while self.lastack+self.deslead>self.lastsent:
                chunk=self.file.read(self.chunk)
                if not chunk: #No more to read:
                    break
                self.sock.sendto(str(BCSPPacket(self.sid, self.service, BCSP.TMIT, sptr=self.lastsent, data=chunk)), self.peer)
                self.lastsent+=len(chunk)