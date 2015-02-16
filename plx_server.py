'''
PIM4 -- Python Instant Messenger version 4
plx_server -- Server Plug

Handles administrative tasks with the server itself. This plug has a
limited vocabulary, just as the server does. All the heavy lifting is
done by channel and user plugs.

This is not user-spawneable. It usually is created by a ConnectPlug.
'''

import shlex
import time

from plug import Plug
from tkconsole import Console, STDWIDTH, STDHEIGHT
from util import IsChannel, IsNick, WriteNick, FgBgDict, PrettyMode, StrToMode, PrettyError
from common import ServerTextCommands
import appconfig

from upp.packet import Packet

from plx_channel import ChannelPlug
from plx_user import UserPlug

KA_TIME=10000

class ServerPlug(Plug, ServerTextCommands):
    def __init__(self, app, addr, nick):
        Plug.__init__(self, app)
        self.addr=addr
        self.dead=False
        self.name=str(addr)
        self.nick=nick
        self.channelplugs={}
        self.userplugs={}
        self.tid=self.app.after(KA_TIME, self.KeepAlive)
    def CreateFrame(self, tf):
        tf.Add(self.name, self.addr[0])
        f=tf.frame[self.name]
        self.console=Console(f, width=STDWIDTH, height=STDHEIGHT, wrap='word')
        self.console.pack(fill='both', expand=1)
    def TFName(self):
        return self.name
    def Discard(self):
        Plug.Discard(self)
        self.app.after_cancel(self.tid)
        self.SendTo(Packet('Desync'))
    def SendTo(self, pkt):
        if not self.dead:
            self.sock.SendTo(self.addr, pkt)
    def CheckLen(self, l, reqlen, *args):
        if len(l)<reqlen:
            self.console.writeln(appconfig.get('STRS', 'TOOFEW')%{'args': len(l), 'needed': reqlen, 'argname': args[len(l)]}, FgBgDict(appconfig.get('CLIENT', 'TOOFEW_FG'), appconfig.get('CLIENT', 'TOOFEW_BG')))
            return False
        elif len(l)>reqlen:
            self.console.writeln(appconfig.get('STRS', 'TOOMANY')%{'args': len(l), 'needed': reqlen}, FgBgDict(appconfig.get('CLIENT', 'TOOMANY_FG'), appconfig.get('CLIENT', 'TOOMANY_BG')))
            return False
        return True
    def KeepAlive(self):
        self.SendTo(Packet('KeepAlive'))
        self.tid=self.app.after(KA_TIME, self.KeepAlive)
    def cmd_Join(self, pkt, addr):
        if addr!=self.addr:
            return
        if hasattr(pkt, 'source'): #Then it's not us...let the channel figure it out
            return
        self.channelplugs[pkt.target]=ChannelPlug(self.app, self, pkt.target)
        self.app.AddPlug(self.channelplugs[pkt.target])
        self.app.SetCurPlug(self.channelplugs[pkt.target])
    def cmd_Part(self, pkt, addr):
        if addr!=self.addr:
            return
        if hasattr(pkt, 'source'):
            return
        self.console.writeln(appconfig.get('STRS', 'SELFPARTED')%pkt.attrs, FgBgDict(appconfig.get('CLIENT', 'SELFPARTED_FG'), appconfig.get('CLIENT', 'SELFPARTED_BG')))
        if pkt.target not in self.channelplugs:
            return
        self.app.RemPlug(self.channelplugs[pkt.target])
        self.app.AlertPlug(self)
    def cmd_Msg(self, pkt, addr):
        if addr!=self.addr:
            return
        if pkt.target=='~' and not pkt.sonic:
            WriteNick(self.console, pkt.source)
            self.console.writeln(pkt.body, FgBgDict(appconfig.get('MSGBODY', 'SPECIAL_FG'), appconfig.get('MSGBODY', 'SPECIAL_BG')))
            self.app.AlertPlug(self)
            return
        if IsNick(pkt.target): #and pkt.target==self.nick?
            if pkt.source in self.userplugs:
                return
            self.userplugs[pkt.source]=UserPlug(self.app, self, pkt.source)
            self.app.AddPlug(self.userplugs[pkt.source])
            self.app.SetCurPlug(self.userplugs[pkt.source])
            self.userplugs[pkt.source].RecvPacket(pkt, addr) #Let it handle this...
    def cmd_Notice(self, pkt, addr):
        if addr!=self.addr:
            return
        if pkt.target=='~' and not pkt.sonic:
            WriteNick(self.console, pkt.source, True)
            self.console.writeln(pkt.body, FgBgDict(appconfig.get('NOTICEBODY', 'SPECIAL_FG'), appconfig.get('NOTICEBODY', 'SPECIAL_BG')))
            self.app.AlertPlug(self)
            return
        if IsNick(pkt.target) and self.app.curplug is self and not pkt.sonic:
            WriteNick(self.console, pkt.source, True)
            self.console.writeln(pkt.body, FgBgDict(appconfig.get('NOTICEBODY', 'FG'), appconfig.get('NOTICEBODY', 'BG')))
            self.app.AlertPlug(self)
    def cmd_Kill(self, pkt, addr):
        if addr!=self.addr:
            return
        if not hasattr(pkt, 'client'): #Uh oh...we're being killed...
            self.dead=True
            self.console.writeln(appconfig.get('STRS', 'KILLED')%pkt.attrs, FgBgDict(appconfig.get('CLIENT', 'KILLED_FG'), appconfig.get('CLIENT', 'KILLED_BG')))
            self.app.AlertPlug(self)
    def cmd_List(self, pkt, addr):
        if addr!=self.addr:
            return
        if not hasattr(pkt, 'target'):
            self.console.writeln(appconfig.get('STRS', 'LBEGIN_CHAN'), FgBgDict(appconfig.get('CLIENT', 'LBEGIN_CHAN_FG'), appconfig.get('CLIENT', 'LBEGIN_CHAN_BG')))
            for chname in pkt.list:
                self.console.writeln(chname, FgBgDict(appconfig.get('LIST', 'CHAN_FG'), appconfig.get('LIST', 'CHAN_BG')))
            self.app.AlertPlug(self)
    def cmd_Delete(self, pkt, addr):
        if addr!=self.addr:
            return
        self.console.writeln(appconfig.get('STRS', 'DELETE')%pkt.attrs, FgBgDict(appconfig.get('CLIENT', 'DELETE_FG'), appconfig.get('CLIENT', 'DELETE_BG')))
        self.app.AlertPlug(self)
    def cmd_Kick(self, pkt, addr): #We handle this here because the server has already sent Part
        if addr!=self.addr: #and thus the ChannelPlug is already gone.
            return #However, this is only if we're the kicked client.
        if self.nick==pkt.client:
            self.console.writeln(appconfig.get('STRS', 'SELFKICKED')%pkt.attrs, FgBgDict(appconfig.get('CLIENT', 'SELFKICKED_FG'), appconfig.get('CLIENT', 'SELFKICKED_BG')))
            self.app.AlertPlug(self)
    def cmd_Mode(self, pkt, addr):
        if addr!=self.addr:
            return
        if not hasattr(pkt, 'target'):
            if hasattr(pkt, 'list'):
                #List of user modes for a client
                self.console.writeln(appconfig.get('STRS', 'UMODES')%pkt.attrs, FgBgDict(appconfig.get('MODE', 'LUMODES_FG'), appconfig.get('MODE', 'LUMODES_BG')))
                for mode in pkt.list:
                    self.console.writeln(PrettyMode(mode), FgBgDict(appconfig.get('MODE', 'LUMODE_FG'), appconfig.get('MODE', 'LUMODE_BG')))
            elif hasattr(pkt, 'set'):
                pkt.set=PrettyMode(pkt.set)
                self.console.writeln(appconfig.get('STRS', 'MODESET')%pkt.attrs, FgBgDict(appconfig.get('MODE', 'SET_FG'), appconfig.get('MODE', 'SET_BG')))
            elif hasattr(pkt, 'unset'):
                pkt.unset=PrettyMode(pkt.unset)
                self.console.writeln(appconfig.get('STRS', 'MODEUNSET')%pkt.attrs, FgBgDict(appconfig.get('MODE', 'UNSET_FG'), appconfig.get('MODE', 'UNSET_BG')))
            else:
                self.console.writeln(appconfig.get('STRS', 'UNREC')%{'object': 'mode packet'}, FgBgFict(appconfig.get('CLIENT', 'UNREC_FG'), appconfig.get('CLIENT', 'UNREC_BG')))
            self.app.AlertPlug(self)
    def cmd_Error(self, pkt, addr):
        if addr!=self.addr or self.app.curplug is not self:
            return
        self.console.writeln(appconfig.get('STRS', 'ERROR')%{'err': PrettyError(pkt.code), 'desc': pkt.desc}, FgBgDict(appconfig.get('CLIENT', 'ERR_FG'), appconfig.get('CLIENT', 'ERR_BG')))
        self.app.AlertPlug(self)
    def cmd_ListClients(self, pkt, addr):
        if addr!=self.addr:
            return
        self.console.writeln(appconfig.get('STRS', 'CLIENTS'), FgBgDict(appconfig.get('CLIENT', 'CLIENTS_FG'), appconfig.get('CLIENT', 'CLIENTS_BG')))
        for k, v in pkt.clients.iteritems():
            d={'client': k}
            d['peer']=v['peer']
            self.console.writeln(appconfig.get('STRS', 'CLIENT')%d, FgBgDict(appconfig.get('CLIENT', 'CLIENT_FG'), appconfig.get('CLIENT', 'CLIENT_BG')))
            for mode in v['modes']:
                self.console.writeln(appconfig.get('STRS', 'CLIENT_MODE')%{'mode': PrettyMode(mode)}, FgBgDict(appconfig.get('CLIENT', 'CLIENT_MODE_FG'), appconfig.get('CLIENT', 'CLIENT_MODE_BG')))
        self.app.AlertPlug(self)
    def cmd_DebugSnapshot(self, pkt, addr):
        if addr!=self.addr:
            return
        self.console.writeln(appconfig.get('STRS', 'DSNAP'), FgBgDict(appconfig.get('CLIENT', 'DSNAP_FG'), appconfig.get('CLIENT', 'DSNAP_BG')))
        self.console.writeln(appconfig.get('STRS', 'DSNAP_CLIENTS'), FgBgDict(appconfig.get('CLIENT', 'DSNAP_CLIENTS_FG'), appconfig.get('CLIENT', 'DSNAP_CLIENTS_BG')))
        for k, v in pkt.clients.iteritems():
            d={'client': k}
            d['peer']=v['peer']
            self.console.writeln(appconfig.get('STRS', 'DSNAP_CLIENT')%d, FgBgDict(appconfig.get('CLIENT', 'DSNAP_CLIENT_FG'), appconfig.get('CLIENT', 'DSNAP_CLIENT_BG')))
            self.console.writeln(appconfig.get('STRS', 'DSNAP_CLIENT_MODES'), FgBgDict(appconfig.get('CLIENT', 'DSNAP_CLIENT_MODES_FG'), appconfig.get('CLIENT', 'DSNAP_CLIENT_MODES_BG')))
            for mode in v['modes']:
                self.console.writeln(appconfig.get('STRS', 'DSNAP_CLIENT_MODE')%{'mode': PrettyMode(mode)}, FgBgDict(appconfig.get('CLIENT', 'DSNAP_CLIENT_MODE_FG'), appconfig.get('CLIENT', 'DSNAP_CLIENT_MODE_BG')))
            self.console.writeln(appconfig.get('STRS', 'DSNAP_CLIENT_CHANNELS'), FgBgDict(appconfig.get('CLIENT', 'DSNAP_CLIENT_CHANNELS_FG'), appconfig.get('CLIENT', 'DSNAP_CLIENT_CHANNELS_BG')))
            for chan in v['channels']:
                self.console.writeln(appconfig.get('STRS', 'DSNAP_CLIENT_CHAN')%chan, FgBgDict(appconfig.get('CLIENT', 'DSNAP_CLIENT_CHAN_FG'), appconfig.get('CLIENT', 'DSNAP_CLIENT_CHAN_BG')))
                self.console.writeln(appconfig.get('STRS', 'DSNAP_CLIENT_CHAN_MODES'), FgBgDict(appconfig.get('CLIENT', 'DSNAP_CLIENT_CHAN_MODES_FG'), appconfig.get('CLIENT', 'DSNAP_CLIENT_CHAN_MODES_BG')))
                for mode in chan['modes']:
                    self.console.writeln(appconfig.get('STRS', 'DSNAP_CLIENT_CHAN_MODE')%{'mode': PrettyMode(mode)}, FgBgDict(appconfig.get('CLIENT', 'DSNAP_CLIENT_CHAN_MODE_FG'), appconfig.get('CLIENT', 'DSNAP_CLIENT_CHAN_MODE_BG')))
                self.console.writeln(appconfig.get('STRS', 'DSNAP_CLIENT_CHAN_UCMODES'), FgBgDict(appconfig.get('CLIENT', 'DSNAP_CLIENT_CHAN_UCMODES_FG'), appconfig.get('CLIENT', 'DSNAP_CLIENT_CHAN_UCMODES_BG')))
                for mode in chan['ucmodes']:
                    self.console.writeln(appconfig.get('STRS', 'DSNAP_CLIENT_CHAN_UCMODE')%{'mode': PrettyMode(mode)}, FgBgDict(appconfig.get('CLIENT', 'DSNAP_CLIENT_CHAN_UCMODE_FG'), appconfig.get('CLIENT', 'DSNAP_CLIENT_CHAN_UCMODE_BG')))
        self.console.writeln(appconfig.get('STRS', 'DSNAP_CHANNELS'), FgBgDict(appconfig.get('CLIENT', 'DSNAP_CHANNELS_FG'), appconfig.get('CLIENT', 'DSNAP_CHANNELS_BG')))
        for k, v in pkt.channels.iteritems():
            self.console.writeln(appconfig.get('STRS', 'DSNAP_CHANNEL')%v, FgBgDict(appconfig.get('CLIENT', 'DSNAP_CHANNEL_FG'), appconfig.get('CLIENT', 'DSNAP_CHANNEL_BG')))
            self.console.writeln(appconfig.get('STRS', 'DSNAP_CHAN_MODES'), FgBgDict(appconfig.get('CLIENT', 'DSNAP_CHAN_MODES_FG'), appconfig.get('CLIENT', 'DSNAP_CHAN_MODES_BG')))
            for mode in v['modes']:
                self.console.writeln(appconfig.get('STRS', 'DSNAP_CHAN_MODE')%{'mode': PrettyMode(mode)}, FgBgDict(appconfig.get('CLIENT', 'DSNAP_CHAN_MODE_FG'), appconfig.get('CLIENT', 'DSNAP_CHAN_MODE_BG')))
            self.console.writeln(appconfig.get('STRS', 'DSNAP_CHAN_CLIENTS'), FgBgDict(appconfig.get('CLIENT', 'DSNAP_CHAN_CLIENTS_FG'), appconfig.get('CLIENT', 'DSNAP_CHAN_CLIENTS_BG')))
            for client in v['clients']:
                self.console.writeln(appconfig.get('STRS', 'DSNAP_CHAN_CLIENT')%{'client': client}, FgBgDict(appconfig.get('CLIENT', 'DSNAP_CHAN_CLIENT_FG'), appconfig.get('CLIENT', 'DSNAP_CHAN_CLIENT_BG')))
        self.app.AlertPlug(self)
    def cmd_Ping(self, pkt, addr):
        if addr!=self.addr:
            return
        self.SendTo(Packet('Pong', stime=time.time()))
    def cmd_Pong(self, pkt, addr):
        if addr!=self.addr:
            return
        pkt.latency=time.time()-pkt.stime
        self.console.writeln(appconfig.get('STRS', 'PONG')%pkt.attrs, FgBgDict(appconfig.get('CLIENT', 'PONG_FG'), appconfig.get('CLIENT', 'PONG_BG')))