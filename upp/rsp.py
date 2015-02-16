'''
UPP -- Unified Packet Protocol
RSP -- Reliable Streaming Protocol

This is the TCP of UPP. It is much simpler and to the point, and the
module reflects this.

To use it, you must wrap a socket in a StreamSession. (You can wrap
the socket indefinitely with as many StreamSessions as needed; this
module will assign an unused stream identifier to the StreamSession.)

The serverside (the one who is willing to start StreamSessions) will
probably have any number of StreamChannels ready to start a stream.
They are identified by name, which is usually a service name, and this
name must be provided by the client when it starts a StreamSession.

Each StreamChannel defers itself to a StreamHandler. The handler is
responsible for implementing the useful side of the stream's function;
the channel just ensures that RSP sessions can be initiated (and the
handler can actually prevent this from happening using certain hooks).
One handler exists per session; the handlers can safely store private
data on self.

Reliable Streaming Protocol is a simplex communication protocol. In
order to communicate in duplex (or, rather, dual-simplex), both peers
must simultaneously fulfil the roles of "client" and "server". This
is easily done as long as both implement the proper services, because
RSP is meant to be multiplexed over one connection between the peers.
'''

from const import *
import uppsocket
import packet

class UPPServerSocket(uppsocket.UPPSocket):
    def __init__(self, sock):
        self.sock=uppsocket.UPPSocket.Wrap(sock)
        self.channels=set()
    def AddChannel(self, chan):
        self.channels.add(chan)
    def RemoveChannel(self, chan):
        self.channels.discard(chan)
    def Pump(self):
        pkt, addr=self.RecvFrom()
        if pkt.cmd=='Stream':
            for chan in self.channels:
                if pkt.service==chan.service:
                    chan.Pump(pkt, addr)
                    return None, None
            self.SendTo(addr, packet.Packet(cmd='Stream', resp='Error', sid=pkt.sid, code=RSPERR.NOSERVICE, reason='No service by that name'))
            return None, None
        return pkt, addr

class StreamChannel(object):
    def __init__(self, sock, service, handler, maxsessions=MAX_SESSIONS):
        self.sock=uppsocket.UPPSocket.Wrap(sock)
        self.service=service
        self.handler=handler #Note: this is a type
        self.clients={} #addr tuple -> dict (sid -> handlerinst)
        self.maxsessions=maxsessions
    def Pump(self, pkt, addr):
        if pkt.cmd!='Stream':
            return
        if addr not in self.clients:
            self.clients[addr]={} #Add a session dict if it doesn't exist
        sessions=self.clients[addr]
        if pkt.sid in sessions:
            handler=sessions[pkt.sid]
            if pkt.req=='Sync':
                #A client is resyncing a used sid...
                self.sock.SendTo(addr, packet.Packet(cmd='Stream', resp='Error', sid=pkt.sid, service=self.service, code=RSPERR.DENIED_SID, reason='SID already in use', close=False))
            elif pkt.req=='Close':
                #Client is closing stream...
                #We cannot prevent this from happening; the client has made up their mind already
                #all we can do is inform the handler that this is happening
                handler.Close(pkt)
                self.sock.SendTo(addr, packet.Packet(cmd='Stream', resp='Close', sid=pkt.sid, service=self.service))
                #Goodbye
                del sessions[pkt.sid]
                if not sessions:
                    del self.clients[addr]
            elif pkt.req=='Data':
                #Client is sending some stream data
                if handler.Data(pkt):
                    #A true return here means the handler wants to close the connection
                    self.sock.SendTo(addr, packet.Packet(cmd='Stream', resp='Close', sid=pkt.sid, service=self.service))
                    del sessions[pkt.sid]
                    if not sessions:
                        del self.clients[addr]
                else:
                    #False return means ack
                    self.sock.SendTo(addr, packet.Packet(cmd='Stream', resp='Ack', sid=pkt.sid, service=self.service))
            else:
                #Unknown command
                self.sock.SendTo(addr, packet.Packet(cmd='Stream', resp='Error', sid=pkt.sid, service=self.sevice, code=RSPERR.BADREQ, reason='No such request', close=False))
        else:
            #A client we know, but with an unknown SID...could be a new connection
            if pkt.req=='Sync':
                #Client is trying to sync a new SID
                cntsessions=0
                for sess in self.clients.itervalues():
                    cntsessions+=len(sess)
                if cntsessions>=self.maxsessions:
                    #We can't accept this session, sorry
                    self.sock.SendTo(addr, packet.Packet(cmd='Stream', resp='Close', sid=pkt.sid, service=self.service))
                    del sessions[pkt.sid]
                    if not sessions:
                        del self.clients[addr]
                handler=self.handler(self, addr, pkt.sid)
                if handler.Sync(pkt):
                    #The handler can't accept this connection, abort
                    self.sock.SendTo(addr, packet.Packet(cmd='Stream', resp='Close', sid=pkt.sid, service=self.service))
                    del sessions[pkt.sid]
                    if not sessions:
                        del self.clients[addr]
                else:
                    #Finalize the connection
                    self.sock.SendTo(addr, packet.Packet(cmd='Stream', resp='Sync', sid=pkt.sid, service=self.service))
            elif pkt.req in ('Close', 'Data'):
                #The stream identified isn't open
                self.sock.SendTo(addr, packet.Packet(cmd='Stream', resp='Error', sid=pkt.sid, service=self.service, code=RSPERR.DENIED_SID, reason='Session not open', close=True))
            else:
                self.sock.SendTo(addr, packet.Packet(cmd='Stream', resp='Error', sid=pkt.sid, service=self.service, code=RSPERR.BADREQ, reason='No such request', close=False))

class BaseHandler(object): #Just a little helper
    def __init__(self, channel, addr, sid):
        self.channel=channel
        self.addr=addr
        self.sid=sid
    def Sync(self, pkt):
        return False #To allow normal connection
    def Data(self, pkt):
        return False #To retain the connection
    def Close(self, pkt):
        pass #We cannot influence the client's decision to close

class UPPClientSocket(uppsocket.UPPSocket):
    def __init__(self, sock):
        self.sock=uppsocket.UPPSocket.Wrap(sock)
        self.sessions=set()
    def AddSession(self, sess):
        self.sessions.add(sess)
    def RemoveSession(self, sess):
        self.sessions.discard(sess)
    def NewSession(self, peer, service, sid=None, connect=True):
        sess=StreamSession(self.sock, peer, service, sid, connect)
        self.AddSession(sess)
        return sess
    def Pump(self):
        pkt, addr=self.sock.RecvFrom()
        if pkt.cmd=='Stream':
            for sess in self.sessions:
                if pkt.sid==sess.sid:
                    sess.Pump(pkt, addr)
                    return None, None
            #Unknown sid, ignore it
            return None, None
        return pkt, addr

class StreamSession(object):
    SID=1
    def __init__(self, sock, peer, service, sid=None, connect=True):
        self.sock=uppsocket.UPPSocket.Wrap(sock)
        self.peer=peer
        self.connected=False #Whether or not we established a connection
        self.waiting=False #Whether or not we're waiting for an Ack
        self.buffer=[] #Data that can't be pushed because we're waiting
        self.listenstate=RSPLS.NONE
        self.service=service
        if sid is None:
            self.sid=self.SID
            self.SID+=1
        else:
            self.sid=sid
        if connect:
            self.Connect()
    def Connect(self, **kwargs):
        if not self.connected:
            self.sock.SendTo(self.peer, packet.Packet(cmd='Stream', req='Sync', sid=self.sid, service=self.service, **kwargs))
            self.listenstate=RSPLS.SYNC
    def Pump(self, pkt, addr):
        if self.listenstate=RSPLS.SYNC:
            self.listenstate=RSPLS.NONE
            if pkt.resp=='Error':
                if pkt.close:
                    self.connected=False
            elif pkt.resp!='Sync':
                raise TypeError('Server did not respond with Sync or Error')
            #If we got here, all went well.
            self.connected=True
        elif self.listenstate=RSPLS.ACK:
            self.listenstate=RSPLS.NONE
            if pkt.resp=='Close':
                self.connected=False
            elif pkt.resp=='Ack':
                if self.buffer:
                    self.SendTo(self.peer, self.buffer.pop(0))
                    self.listenstate=RSPLS.ACK
            elif pkt.resp=='Error':
                if pkt.close:
                    self.connected=False
            else:
                raise TypeError('Server did not respond with Close, Ack, or Error')
        elif self.listenstate==RSPLS.CLOSE:
            self.listenstate=RSPLS.NONE
            self.connected=False #No matter what
    def Push(self, data):
        if not self.waiting:
            self.sock.SendTo(self.peer, packet.Packet(cmd='Stream', req='Data', sid=self.sid, service=self.service, data=data))
            self.listenstate=RSPLS.ACK
        else:
            self.buffer.append(packet.Packet(cmd='Stream', req='Data', sid=self.sid, service=self.service, data=data))
    def PushDict(self, **kwargs):
        if not self.waiting:
            self.sock.SendTo(self.peer, packet.Packet(cmd='Stream', req='Data', sid=self.sid, service=self.service, **kwargs))
            self.listenstate=RSPLS.ACK
        else:
            self.buffer.append(packet.Packet(cmd='Stream', req='Data', sid=self.sid, service=self.service, **kwargs))
    def Close(self, **kwargs):
        if self.connected:
            self.sock.SendTo(self.peer, packet.Packet(cmd='Stream', req='Close', sid=self.sid, service=self.service, **kwargs))
            self.listenstate=RSPLS.CLOSE