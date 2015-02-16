'''
upp -- Unified Packet Protocol
ex_fpp -- Extension: File Push Protocol

Uses RSP to push a file from one peer to another.

It doesn't matter how this is set up; the receiver can have their FPP
channel open all the time, or can have it selectively open after
agreeing to the transfer using another stream (or protocol for that
matter). The important part is that:
-A FPP channel is open on the receiver.
-The FPP session can connect to this channel from the sender.

We'll buffer the file ahead a little for particularly fast
connections.

(Note: to "secure" your FPP channel from just allowing anyone to
upload a file to it, subclass the FPPHandler in this module and
override the .Sync() method to return True when you do not want the
client whose address is self.addr, session is self.sid, and Sync
packet is the only argument to connect. You must call the FPPHandler's
method, however, if you consent to the connection, because it sets up
important state information from the packet. If this method returns
True, you should too; it usually means there was a bad input.)

You can play with the FPPSession's .chunksize if you want to play with
chunk sizing. It starts off equal to const.FPP_CHUNK, but you can
increase or decrease the value if you are aware what you are doing.
Particularly bandwidth-sensitive clients may find certain chunk sizes
to be benificial, while others are problematic. See const for the
reason why const.FPP_CHUNK, by default, is 1024.
'''

import os

import rsp
from const import *

#On the upstream side...

class FPPHandler(rsp.BaseHandler):
    def Sync(self, pkt):
        if ':' in pkt.filename or '/' in pkt.filename or '\\' in pkt.filename:
            return True #We can only specify the filename, not a path.
        fname=pkt.filename
        basefname=fname
        n=0
        while os.path.exists(fname):
            #Mangle the filename a little
            fname=str(n)+basefname
            n+=1
            if n>500: #That's just ridiculous...
                return True #Too many files by that name
        self.fname=fname
        self.f=open(fname, 'w')
        self.done=False
    def Data(self, pkt):
        if pkt.op=='Chunk':
            if not self.done:
                self.f.write(pkt.chunk)
        elif pkt.op=='Done':
            self.done=True
            return True
    def Close(self, pkt):
        self.f.close()
        if not self.done:
            os.rename(self.fname, self.fname+'-incomplete')

#And downstream...

class FPPSession(rsp.StreamSession):
    def __init__(self, sock, peer, file, fname, service=SERV.FPP, sid=None):
        rsp.StreamSession.__init__(self, sock, peer, service, sid, False)
        self.file=file
        self.fname=fname
        self.chunksize=FPP_CHUNK
    def Start(self):
        self.Connect(filename=self.fname)
    def Transfer(self, bufahead=3):
        while len(self.buffer)<bufahead:
            chunk=self.file.read(self.chunksize)
            if not chunk:
                if not self.buffer:
                    self.PushDict(op='Done') #And we'll close shortly
            self.PushDict(op='Chunk', chunk=chunk)