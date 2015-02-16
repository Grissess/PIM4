'''
PIM4 -- Python Instant Messenger version 4
server -- Server

The actual server, which:
-authenticates clients.
-manages clients.
-manages channels.
-interprets server-wide commands.
'''

SERVER_UNAME='.server'
PIM4_PORT=45903
PING_TIME=20 #seconds before we consider pinging the client to see if they're there
KILL_TIME=30 #seconds after which we should assume the client is dead
KILL_RES=1 #second interval at which the KillThread is fired, providing resolution of time
QUANTUM=0.001 #Number of seconds to wait while we're making sure the pump is shutting down
PUMP_TIMEOUT=10 #Number of seconds to wait for pump shutdown AT MAX, the pump will continue
#regardless after this timeout expires (for the sake of maintaining a healthy socket).
MAXWAIT=0.1 #Maximum wait in seconds for acquiring the pump spinlock, especially if the
#pump thread isn't receiving packets (which is most of the time)

import socket
import time
import threading

from sv_client import Client
from modes import Modes, MODE
from error import ERROR
from auth import IniFileAuth
from channel import Channel
from pump import PacketPump
from sext import LoadExtensions

from upp.uppsocket import UPPSocket
from upp.packet import Packet

def _Event__threadsWaiting(self):
    return len(self._Event__cond._Condition__waiters)
threading._Event.threadsWaiting=_Event__threadsWaiting

class Server(object):
    def __init__(self, sock, auth):
        self.sock=UPPSocket.Wrap(sock)
        self.auth=auth
        self.clients={}
        self.channels={}
        self.sexts=[]
        self.pumpevent=threading.Event()
        self.pumpevent.set()
    def Start(self):
        threading.Thread(target=self._KillThread, args=()).start()
    def AddClient(self, cli):
        self.clients[cli.nick]=cli
        cli.lasttime=time.time()
    def RemoveClient(self, cli):
        if cli.nick in self.clients:
            del self.clients[cli.nick]
    def HasClient(self, cli):
        return cli.nick in self.clients
    def AddChannel(self, chn):
        self.channels[chn.name]=chn
    def RemoveChannel(self, chn):
        if chn.name in self.channels:
            del self.channels[chn.name]
    def HasChannel(self, chn):
        return chn.name in self.channels
    def AddSExt(self, sext):
        if sext not in self.sexts:
            self.sexts.append(sext)
    def RemoveSExt(self, sext):
        try:
            self.sexts.remove(sext)
        except ValueError:
            pass
    def IterSExts(self, method, *args, **kwargs):
        for sext in self.sexts:
            getattr(sext, method)(*args, **kwargs)
    def ShortIterSExts(self, method, *args, **kwargs):
        for sext in self.sexts:
            ret=getattr(sext, method)(*args, **kwargs)
            if ret:
                return ret
        return None
    def CheckParams(self, pkt, *args):
        for arg in args:
            if not hasattr(pkt, arg):
                return False
        return True
    def ClientByAddr(self, addr):
        for cli in self.clients.values():
            if cli.peer==addr:
                return cli
    def TakePacket(self, pkt, addr):
        print 'PUMP: Taken packet', repr(pkt)
        if not self.pumpevent.wait(PUMP_TIMEOUT):
            print 'WARNING: Pump event has deadlocked, we are continuing anyways...'
            self.ReleasePumpLock()
        print 'PUMP: Processing packet', repr(pkt)
        if self.ShortIterSExts('PreRecvPacket', pkt, addr):
            print 'PUMP: Bailed on PreRecvPacket (taken by SExt)'
            return
        cli=self.ClientByAddr(addr)
        if pkt.cmd=='Sync':
            self.cmd_Sync(cli, pkt, addr)
            print 'PUMP: Finished Sync'
            return
        elif cli is None:
            self.sock.SendTo(addr, Packet('Error', code=ERROR.PROTOCOL, desc='Please Sync first.'))
            return
        cli.lasttime=time.time()
        if self.ShortIterSExts('PreDispatchPacket', cli, pkt):
            return
        if hasattr(pkt, 'target'):
            if pkt.target in self.clients:
                cl=self.clients[pkt.target]
                if cl.modes.Check(MODE.SILENT):
                    cli.Error(ERROR.DEVOICED, 'Client does not want to receive C2C packets.')
                    return
                pkt.source=cli.nick
                cl.sock.SendTo(cl.peer, pkt)
            elif pkt.target in self.channels:
                chn=self.channels[pkt.target]
                if hasattr(chn, 'cmd_'+pkt.cmd):
                    getattr(chn, 'cmd_'+pkt.cmd)(cli, pkt)
                else:
                    cli.Error(ERROR.PROTOCOL, 'Command not understood by target.')
            else:
                cli.Error(ERROR.NOTFOUND, 'Cannot find specified target.')
        else:
            if hasattr(self, 'cmd_'+pkt.cmd):
                getattr(self, 'cmd_'+pkt.cmd)(cli, pkt)
            else:
                if not self.ShortIterSExts('UnknownPacket', cli, pkt):
                    cli.Error(ERROR.PROTOCOL, 'Command not understood.')
    def TakeError(self, pkt, addr):
        print 'Error on', pkt
        for cl in self.clients.values():
            cl.Msg(SERVER_UNAME, '~', 'The server has experienced an error. Please be aware that there may be operating inconsistencies. (It would be a good idea to disconnect.)')
    def AcquirePumpLock(self):
        self.pumpevent.clear()
        sttime=time.time()
        while (not self.pumpevent.threadsWaiting()) and time.time()<sttime+MAXWAIT:
            time.sleep(QUANTUM)
    def ReleasePumpLock(self):
        self.pumpevent.set()
    def _KillThread(self):
        while True:
            time.sleep(KILL_RES)
            print 'KT: Tick'
            self.AcquirePumpLock()
            print 'KT: Acquired pump spinlock'
            clis=self.clients.copy()
            print 'KT: Processing', len(clis), 'clients'
            for cl in clis.values():
                if time.time()-cl.lasttime>KILL_TIME:
                    self.RemoveClient(cl)
                    print 'Killed', cl.nick, 'for timeout'
                    continue
                if time.time()-cl.lasttime>PING_TIME:
                    cl.Packet('Ping', stime=time.time())
                    print 'Pinging', cl.nick
            self.ReleasePumpLock()
            print 'KT: Released'
    def cmd_Sync(self, cli, pkt, addr=None):
        if cli is not None or addr is None:
            cli.Error(ERROR.PROTOCOL, 'Already Synced. Desync first.')
            cli.Packet('Sync', result=False)
            return
        cli=Client(self.sock, addr, '.DEFAULT_NICK')
        if not self.CheckParams(pkt, 'nick'):
            cli.Error(ERROR.PROTOCOL, 'Malformed Sync packet.')
            cli.Packet('Sync', result=False)
            return
        if pkt.nick in self.clients:
            cli.Error(ERROR.EXISTS, 'Nick taken. Use another one.')
            cli.Packet('Sync', result=False)
            return
        cli.nick=pkt.nick
        cli.lasttime=time.time()
        if self.auth.Authenticate(cli, pkt):
            self.clients[cli.nick]=cli
            cli.Packet('Sync', result=True)
        else:
            cli.Error(ERROR.ACCESS, 'Authentication failed. You must Sync again.')
            cli.Packet('Sync', result=False)
    def cmd_Desync(self, cli, pkt):
        cli.Msg('.server', cli.nick, 'Goodbye.')
        for chn in self.channels.values():
            if cli in chn.clients:
                chn.RemoveClient(cli)
                for cl in chn.clients:
                    cl.Packet('Part', target=chn.name, source=cli.nick)
        try:
            del self.clients[cli.nick]
        except KeyError:
            cli.Error(ERROR.NOTFOUND, 'Oops; cannot find your client entry. You\'re disconnected anyways.')
    def cmd_Mode(self, cli, pkt):
        if not self.CheckParams(pkt, 'client'):
            cli.Error(ERROR.PROTOCOL, 'Malformed Mode packet.')
            return
        if pkt.client not in self.clients:
            cli.Error(ERROR.NOTFOUND, 'Cannot find client by that nick.')
            return
        cl=self.clients[pkt.client]
        if not (hasattr(pkt, 'set') or hasattr(pkt, 'unset')):
            cli.Packet('Mode', client=cl.nick, list=list(cl.modes))
            return
        if cl!=cli and not cli.IsSop():
            cli.Error(ERROR.ACCESS, 'You may not set other clients\' modes.')
            return
        mode=(pkt.set if hasattr(pkt, 'set') else pkt.unset)
        if mode in MODE.UNEEDSOP and not cli.IsSop():
            cli.Error(ERROR.ACCESS, 'You may not set that mode.')
            return
        if hasattr(pkt, 'set'):
            cl.modes.Set(mode)
            cli.Packet('Mode', client=cl.nick, source=cli.nick, set=mode)
            cl.Packet('Mode', client=cl.nick, source=cli.nick, set=mode)
        else:
            cl.modes.Unset(mode)
            cli.Packet('Mode', client=cl.nick, source=cli.nick, unset=mode)
            cl.Packet('Mode', client=cl.nick, source=cli.nick, unset=mode)
    def cmd_Create(self, cli, pkt):
        if not self.CheckParams(pkt, 'channel'):
            cli.Error(ERROR.PROTOCOL, 'Malformed Create packet.')
            return
        if not pkt.channel:
            cli.Error(ERROR.PROTOCOL, 'NULL channel name.')
            return
        if pkt.channel in self.channels:
            cli.Error(ERROR.EXISTS, 'Channel already exists.')
            return
        if pkt.channel[0] not in '@#':
            cli.Error(ERROR.PROTOCOL, 'Invalid channel name.')
            return
        self.channels[pkt.channel]=Channel(self, pkt.channel)
        self.channels[pkt.channel].AddClient(cli)
        self.channels[pkt.channel].Op(cli)
        cli.Packet('Join', target=pkt.channel)
    def cmd_Delete(self, cli, pkt):
        if not cli.IsSop():
            cli.Error(ERROR.ACCESS, 'You may not use this command.')
            return
        if not self.CheckParams(pkt, 'channel'):
            cli.Error(ERROR.PROTOCOL, 'Malformed Delete packet.')
            return
        if pkt.channel not in self.channels:
            cli.Error(ERROR.NOTFOUND, 'Channel not found.')
            return
        chn=self.channels[pkt.channel]
        for cl in chn.clients:
            cl.Packet('Part', target=chn.name)
            cl.Packet('Delete', channel=chn.name)
    def cmd_Bring(self, cli, pkt):
        if not cli.IsSop():
            cli.Error(ERROR.ACCESS, 'You may not use this command.')
            return
        if not self.CheckParams(pkt, 'channel', 'client'):
            cli.Error(ERROR.PROTOCOL, 'Malformed Bring packet.')
            return
        if pkt.channel not in self.channels:
            cli.Error(ERROR.NOTFOUND, 'Channel not found.')
            return
        if pkt.client not in self.clients:
            cli.Error(ERROR.NOTFOUND, 'Client not found.')
            return
        chn=self.channels[pkt.channel]
        cl=self.clients[pkt.client]
        cl.Packet('Join', target=chn.name)
        for c in chn.clients:
            c.Packet('Join', source=cl.nick, target=chn.name)
        chn.AddClient(cl)
    def cmd_List(self, cli, pkt):
        cli.Packet('List', list=[ch.name for ch in self.channels.values() if not ch.modes.Check(MODE.SECRET)])
    def cmd_Kill(self, cli, pkt):
        if not cli.IsSop():
            cli.Error(ERROR.ACCESS, 'You may not use this command.')
            return
        if not self.CheckParams(pkt, 'client'):
            cli.Error(ERROR.PROTOCOL, 'Malformed Kill packet.')
            return
        if pkt.client not in self.clients:
            cli.Error(ERROR.NOTFOUND, 'Client not found.')
            return
        cl=self.clients[pkt.client]
        cl.Packet('Kill', source=cli.nick)
        for ch in self.channels.values():
            if ch.HasClient(cl):
                ch.RemoveClient(cl)
                for c in ch.clients:
                    c.Packet('Kill', source=cli.nick, client=cl.nick)
    def cmd_MsgAll(self, cli, pkt):
        if not cli.IsSop():
            cli.Error(ERROR.ACCESS, 'You may not use this command.')
            return
        if not self.CheckParams(pkt, 'body'):
            cli.Error(ERROR.PROTOCOL, 'Malformed MsgAll packet.')
            return
        for cl in self.clients.values():
            cl.Msg(cli.nick, '~', pkt.body)
    def cmd_ListClients(self, cli, pkt):
        if not cli.IsSop():
            cli.Error(ERROR.ACCESS, 'You may not use this command.')
            return
        d=self.clients.copy()
        for k, v in d.items():
            d[k]={'peer': v.peer, 'modes': list(v.modes)}
        cli.Packet('ListClients', clients=d)
    def cmd_DebugSnapshot(self, cli, pkt):
        if not cli.IsSop():
            cli.Error(ERROR.ACCESS, 'You may not use this command.')
            return
        d=self.clients.copy()
        for k, v in d.items():
            d[k]={'peer': v.peer, 'modes': list(v.modes), 'channels': []}
            for chn in self.channels.values():
                if chn.HasClient(v):
                    d[k]['channels'].append({'name': chn.name, 'modes': list(chn.modes), 'ucmodes': list(chn.ucmodes.GetModes(v))})
        e=self.channels.copy()
        for k, v in e.items():
            e[k]={'name': v.name, 'modes': list(v.modes), 'clients': [i.nick for i in v.clients]}
        cli.Packet('DebugSnapshot', clients=d, channels=e)
    def cmd_Chicken(self, cli, pkt):
        cli.Msg(SERVER_UNAME, '~', 'What? Chicken butt. Why? Chicken thigh.')
    def cmd_KeepAlive(self, cli, pkt):
        pass
    def cmd_Ping(self, cli, pkt):
        cli.Packet('Pong', stime=time.time())
    def cmd_Pong(self, cli, pkt):
        pass #Keep-alive in effect

if __name__=='__main__':
    print ' PIM4 Server/Broker '.center(79, '*')
    print ' Grissess the Macookwee '.center(79, '*')
    print 'Will now begin serving on port', PIM4_PORT, 'UDP...'
    sck=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sck.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) #Yes...I went there...
    sck.bind(('', PIM4_PORT))
    serv=Server(sck, IniFileAuth())
    pump=PacketPump(sck)
    pump.SetEntry(serv.TakePacket)
    pump.SetErrorEntry(serv.TakeError)
    print 'Loading extensions...'
    sexts=[i(serv) for i in LoadExtensions()]
    for sext in sexts:
        serv.AddSExt(sext)
    print 'Starting server threads...'
    serv.Start()
    print 'Starting pump...'
    pump.started=True
    pump._PumpThread()