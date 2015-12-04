'''
PIM4 -- Python Instant Messenger version 4
plx_channel -- Channel Plug

Handles a singular connection to a channel.
'''

import shlex

from plug import Plug
import appconfig
from util import IsNick, WriteNick, FgBgDict, PrettyMode, StrToMode, PrettyError
from tkconsole import Console, STDWIDTH, STDHEIGHT
from common import ChannelTextCommands

from upp.packet import Packet

class ChannelPlug(ChannelTextCommands, Plug):
    def __init__(self, app, server, name):
        Plug.__init__(self, app)
        self.server=server
        self.name=name
        self.fqname=self.server.name+self.name
    def CreateFrame(self, tf):
        tf.Add(self.fqname, self.name)
        f=tf.frame[self.fqname]
        self.console=Console(f, width=STDWIDTH, height=STDHEIGHT, wrap='word')
        self.console.pack(fill='both', expand=1)
    def TFName(self):
        return self.fqname
    def CheckLen(self, l, reqlen, *args):
        if len(l)<reqlen:
            self.console.writeln(appconfig.get('STRS', 'TOOFEW')%{'args': len(l), 'needed': reqlen, 'argname': args[len(l)]}, FgBgDict(appconfig.get('CLIENT', 'TOOFEW_FG'), appconfig.get('CLIENT', 'TOOFEW_BG')))
            return False
        elif len(l)>reqlen:
            self.console.writeln(appconfig.get('STRS', 'TOOMANY')%{'args': len(l), 'needed': reqlen}, FgBgDict(appconfig.get('CLIENT', 'TOOMANY_FG'), appconfig.get('CLIENT', 'TOOMANY_BG')))
            return False
        return True
    def cmd_Msg(self, pkt, addr):
        if addr!=self.server.addr:
            return
        if pkt.target==self.name and not pkt.sonic:
            WriteNick(self.console, pkt.source)
            self.console.writeln(pkt.body, FgBgDict(appconfig.get('MSGBODY', 'FG'), appconfig.get('MSGBODY', 'BG')))
            self.app.AlertPlug(self)
    def cmd_Notice(self, pkt, addr):
        if addr!=self.server.addr:
            return
        if IsNick(pkt.target) and self.app.curplug is self and not pkt.sonic:
            WriteNick(self.console, pkt.source, True)
            self.console.writeln(pkt.body, FgBgDict(appconfig.get('NOTICEBODY', 'FG'), appconfig.get('NOTICEBODY', 'BG')))
            self.app.AlertPlug(self)
    def cmd_Join(self, pkt, addr):
        if addr!=self.server.addr:
            return
        if hasattr(pkt, 'source') and pkt.target==self.name:
            self.console.writeln(appconfig.get('STRS', 'JOINED')%pkt.attrs, FgBgDict(appconfig.get('CLIENT', 'JOINED_FG'), appconfig.get('CLIENT', 'JOINED_BG')))
            self.app.AlertPlug(self)
    def cmd_Part(self, pkt, addr):
        if addr!=self.server.addr:
            return
        if hasattr(pkt, 'source') and pkt.target==self.name:
            self.console.writeln(appconfig.get('STRS', 'PARTED')%pkt.attrs, FgBgDict(appconfig.get('CLIENT', 'PARTED_FG'), appconfig.get('CLIENT', 'PARTED_BG')))
            self.app.AlertPlug(self)
    def cmd_List(self, pkt, addr):
        if addr!=self.server.addr:
            return
        if hasattr(pkt, 'target'):
            self.console.writeln(appconfig.get('STRS', 'LBEGIN_NICK'), FgBgDict(appconfig.get('CLIENT', 'LBEGIN_NICK_FG'), appconfig.get('CLIENT', 'LBEGIN_NICK_BG')))
            for nick in pkt.list:
                self.console.writeln(nick, FgBgDict(appconfig.get('LIST', 'NICK_FG'), appconfig.get('LIST', 'NICK_BG')))
            self.app.AlertPlug(self)
    def cmd_Op(self, pkt, addr):
        if addr!=self.server.addr:
            return
        if pkt.target==self.name:
            self.console.writeln(appconfig.get('STRS', 'OP')%pkt.attrs, FgBgDict(appconfig.get('CHAN', 'OP_FG'), appconfig.get('CHAN', 'OP_BG')))
            self.app.AlertPlug(self)
    def cmd_Deop(self, pkt, addr):
        if addr!=self.server.addr:
            return
        if pkt.target==self.name:
            self.console.writeln(appconfig.get('STRS', 'DEOP')%pkt.attrs, FgBgDict(appconfig.get('CHAN', 'DEOP_FG'), appconfig.get('CHAN', 'DEOP_BG')))
            self.app.AlertPlug(self)
    def cmd_Hop(self, pkt, addr):
        if addr!=self.server.addr:
            return
        if pkt.target==self.name:
            self.console.writeln(appconfig.get('STRS', 'HOP')%pkt.attrs, FgBgDict(appconfig.get('CHAN', 'HOP_FG'), appconfig.get('CHAN', 'HOP_BG')))
            self.app.AlertPlug(self)
    def cmd_Dehop(self, pkt, addr):
        if addr!=self.server.addr:
            return
        if pkt.target==self.name:
            self.console.writeln(appconfig.get('STRS', 'DEHOP')%pkt.attrs, FgBgDict(appconfig.get('CHAN', 'DEHOP_FG'), appconfig.get('CHAN', 'DEHOP_BG')))
            self.app.AlertPlug(self)
    def cmd_Kick(self, pkt, addr):
        if addr!=self.server.addr:
            return
        if pkt.target==self.name:
            self.console.writeln(appconfig.get('STRS', 'KICKED')%pkt.attrs, FgBgDict(appconfig.get('CLIENT', 'KICKED_FG'), appconfig.get('CLIENT', 'KICKED_BG')))
            self.app.AlertPlug(self)
    def cmd_Ban(self, pkt, addr):
        if addr!=self.server.addr:
            return
        if pkt.target==self.name:
            self.console.writeln(appconfig.get('STRS', 'BANNED')%pkt.attrs, FgBgDict(appconfig.get('CLIENT', 'BANNED_FG'), appconfig.get('CLIENT', 'BANNED_BG')))
            self.app.AlertPlug(self)
    def cmd_Unban(self, pkt, addr):
        if addr!=self.server.addr:
            return
        if pkt.target==self.name:
            self.console.writeln(appconfig.get('STRS', 'UNBANNED')%pkt.attrs, FgBgDict(appconfig.get('CLIENT', 'UNBANNED_FG'), appconfig.get('CLIENT', 'UNBANNED_BG')))
            self.app.AlertPlug(self)
    def cmd_Devoice(self, pkt, addr):
        if addr!=self.server.addr:
            return
        if pkt.target==self.name:
            self.console.writeln(appconfig.get('STRS', 'DEVOICED')%pkt.attrs, FgBgDict(appconfig.get('CLIENT', 'DEVOICED_FG'), appconfig.get('CLIENT', 'DEVOICED_BG')))
            self.app.AlertPlug(self)
    def cmd_Voice(self, pkt, addr):
        if addr!=self.server.addr:
            return
        if pkt.target==self.name:
            self.console.writeln(appconfig.get('STRS', 'VOICED')%pkt.attrs, FgBgDict(appconfig.get('CLIENT', 'VOICED_FG'), appconfig.get('CLIENT', 'VOICED_BG')))
            self.app.AlertPlug(self)
    def cmd_Mode(self, pkt, addr):
        if addr!=self.server.addr:
            return
        if hasattr(pkt, 'target'):
            if hasattr(pkt, 'list'):
                if hasattr(pkt, 'client'):
                    #List of user modes for a client
                    self.console.writeln(appconfig.get('STRS', 'UCMODES')%pkt.attrs, FgBgDict(appconfig.get('MODE', 'LUCMODES_FG'), appconfig.get('MODE', 'LUCMODES_BG')))
                    for mode in pkt.list:
                        self.console.writeln(PrettyMode(mode), FgBgDict(appconfig.get('MODE', 'LUCMODE_FG'), appconfig.get('MODE', 'LUCMODE_BG')))
                else:
                    self.console.writeln(appconfig.get('STRS', 'CMODES')%pkt.attrs, FgBgDict(appconfig.get('MODE', 'LCMODES_FG'), appconfig.get('MODE', 'LCMODES_BG')))
                    for mode in pkt.list:
                        self.console.writeln(PrettyMode(mode), FgBgDict(appconfig.get('MODE', 'LCMODE_FG'), appconfig.get('MODE', 'LCMODE_BG')))
            elif hasattr(pkt, 'set'):
                pkt.set=PrettyMode(pkt.set)
                self.console.writeln(appconfig.get('STRS', 'CMODESET')%pkt.attrs, FgBgDict(appconfig.get('MODE', 'SET_FG'), appconfig.get('MODE', 'SET_BG')))
            elif hasattr(pkt, 'unset'):
                pkt.unset=PrettyMode(pkt.unset)
                self.console.writeln(appconfig.get('STRS', 'CMODEUNSET')%pkt.attrs, FgBgDict(appconfig.get('MODE', 'UNSET_FG'), appconfig.get('MODE', 'UNSET_BG')))
            else:
                self.console.writeln(appconfig.get('STRS', 'UNREC')%{'object': 'mode packet'}, FgBgDict(appconfig.get('CLIENT', 'UNREC_FG'), appconfig.get('CLIENT', 'UNREC_BG')))
            self.app.AlertPlug(self)
    def cmd_Error(self, pkt, addr):
        if addr!=self.server.addr or self.app.curplug is not self:
            return
        self.console.writeln(appconfig.get('STRS', 'ERROR')%{'err': PrettyError(pkt.code), 'desc': pkt.desc}, FgBgDict(appconfig.get('CLIENT', 'ERR_FG'), appconfig.get('CLIENT', 'ERR_BG')))
        self.app.AlertPlug(self)
    def NoncmdTxt(self, txt):
        WriteNick(self.console, self.server.nick)
        self.console.writeln(txt, FgBgDict(appconfig.get('CLIENT', 'SELFMSG_FG'), appconfig.get('CLIENT', 'SELFMSG_BG')))
        self.server.SendTo(Packet('Msg', target=self.name, body=txt, sonic=False))
