'''
PIM4 -- Python Instant Messenger version 4
common -- Common plug-based code

Some common things that all plugs share.
'''

import shlex
import time

from util import StrToMode, FgBgDict, IsNick
import appconfig

from upp.packet import Packet

class TextCommands(object):
    def CheckLen(self, l, reqlen, *args):
        if len(l)<reqlen:
            self.console.writeln(appconfig.get('STRS', 'TOOFEW')%{'args': len(l), 'needed': reqlen, 'argname': args[len(l)]}, FgBgDict(appconfig.get('CLIENT', 'TOOFEW_FG'), appconfig.get('CLIENT', 'TOOFEW_BG')))
            return False
        elif len(l)>reqlen:
            self.console.writeln(appconfig.get('STRS', 'TOOMANY')%{'args': len(l), 'needed': reqlen}, FgBgDict(appconfig.get('CLIENT', 'TOOMANY_FG'), appconfig.get('CLIENT', 'TOOMANY_BG')))
            return False
        return True

class ServerTextCommands(TextCommands): #requires .nick, .console
    def txt_msg(self, txt):
        parts=shlex.split(txt)
        target=parts[0]
        msg=' '.join(parts[1:])
        self.SendTo(Packet('Msg', target=target, body=msg, sonic=False))
    def txt_notice(self, txt):
        parts=shlex.split(txt)
        target=parts[0]
        msg=' '.join(parts[1:])
        self.SendTo(Packet('Notice', target=target, body=msg, sonic=False))
    def txt_join(self, txt):
        self.SendTo(Packet('Join', target=txt))
    def txt_create(self, txt):
        self.SendTo(Packet('Create', channel=txt))
    def txt_delete(self, txt):
        self.SendTo(Packet('Delete', channel=txt))
    def txt_bring(self, txt):
        parts=shlex.split(txt)
        if not self.CheckLen(parts, 2, 'a nick', 'a channel'):
            return
        self.SendTo(Packet('Bring', client=parts[0], channel=parts[1]))
    def txt_kill(self, txt):
        self.SendTo(Packet('Kill', client=txt))
    def txt_msgall(self, txt):
        self.SendTo(Packet('MsgAll', body=txt))
    def txt_mode(self, txt):
        self.SendTo(Packet('Mode', client=txt))
    def txt_setmode(self, txt):
        parts=shlex.split(txt)
        if not self.CheckLen(parts, 2, 'a nick', 'a mode'):
            return
        try:
            mode=StrToMode(parts[1])
        except AttributeError:
            self.console.writeln(appconfig.get('STRS', 'UNREC')%{'object': 'mode enum'}, FgBgDict(appconfig.get('CLIENT', 'UNREC_FG'), appconfig.get('CLIENT', 'UNREC_BG')))
        else:
            if IsNick(parts[0]):
                self.SendTo(Packet('Mode', client=parts[0], set=mode))
            else:
                self.SendTo(Packet('Mode', target=parts[0], set=mode))
    def txt_unsetmode(self, txt):
        parts=shlex.split(txt)
        if not self.CheckLen(parts, 2, 'a nick', 'a mode'):
            return
        try:
            mode=StrToMode(parts[1])
        except AttributeError:
            self.console.writeln(appconfig.get('STRS', 'UNREC')%{'object': 'mode enum'}, FgBgDict(appconfig.get('CLIENT', 'UNREC_FG'), appconfig.get('CLIENT', 'UNREC_BG')))
        else:
            if IsNick(parts[0]):
                self.SendTo(Packet('Mode', client=parts[0], unset=mode))
            else:
                self.SendTo(Packet('Mode', target=parts[0], unset=mode))
    def txt_list(self, txt):
        self.SendTo(Packet('List'))
    def txt_listclients(self, txt):
        self.SendTo(Packet('ListClients'))
    def txt_chicken(self, txt):
        self.SendTo(Packet('Chicken'))
    def txt_ping(self, txt):
        self.SendTo(Packet('Ping', stime=time.time()))
    def txt_playdead(self, txt):
        if not txt:
            self.dead=True
        else:
            self.dead=False
    def txt_dsnap(self, txt):
        self.SendTo(Packet('DebugSnapshot'))
    def OtherTxt(self, txt):
        self.console.writeln(appconfig.get('STRS', 'UNREC')%{'object': 'command'}, FgBgDict(appconfig.get('CLIENT', 'UNREC_FG'), appconfig.get('CLIENT', 'UNREC_BG')))

class ChannelTextCommands(ServerTextCommands): #requires .server, .name, .console
    def txt_kick(self, txt):
        self.server.SendTo(Packet('Kick', target=self.name, client=txt))
    def txt_ban(self, txt):
        self.server.SendTo(Packet('Ban', target=self.name, client=txt))
    def txt_unban(self, txt):
        self.server.SendTo(Packet('Unban', target=self.name, client=txt))
    def txt_kickban(self, txt):
        self.server.SendTo(Packet('Ban', target=self.name, client=txt))
        self.server.SendTo(Packet('Kick', target=self.name, client=txt))
    def txt_op(self, txt):
        self.server.SendTo(Packet('Op', target=self.name, client=txt))
    def txt_deop(self, txt):
        self.server.SendTo(Packet('Deop', target=self.name, client=txt))
    def txt_hop(self, txt):
        self.server.SendTo(Packet('Hop', target=self.name, client=txt))
    def txt_dehop(self, txt):
        self.server.SendTo(Packet('Dehop', target=self.name, client=txt))
    def txt_list(self, txt):
        self.server.SendTo(Packet('List', target=self.name))
    def txt_listclients(self, txt):
        self.server.SendTo(Packet('ListClients'))
    def txt_ping(self, txt):
        self.server.SendTo(Packet('Ping', stime=time.time()))
    def txt_chicken(self, txt):
        self.server.SendTo(Packet('Chicken'))
    def txt_dsnap(self, txt):
        self.server.SendTo(Packet('DebugSnapshot'))
    def txt_msg(self, txt):
        parts=shlex.split(txt)
        target=parts[0]
        msg=' '.join(parts[1:])
        self.server.SendTo(Packet('Msg', target=target, body=msg, sonic=False))
    def txt_notice(self, txt):
        parts=shlex.split(txt)
        target=parts[0]
        msg=' '.join(parts[1:])
        self.server.SendTo(Packet('Notice', target=target, body=msg, sonic=False))
    def txt_join(self, txt):
        self.server.SendTo(Packet('Join', target=txt))
    def txt_create(self, txt):
        self.server.SendTo(Packet('Create', channel=txt))
    def txt_delete(self, txt):
        self.server.SendTo(Packet('Delete', channel=txt))
    def txt_bring(self, txt):
        parts=shlex.split(txt)
        if not self.CheckLen(parts, 2, 'a nick', 'a channel'):
            return
        self.server.SendTo(Packet('Bring', client=parts[0], channel=parts[1]))
    def txt_kill(self, txt):
        self.server.SendTo(Packet('Kill', client=txt))
    def txt_msgall(self, txt):
        self.server.SendTo(Packet('MsgAll', body=txt))
    def txt_mode(self, txt):
        if txt:
            self.server.SendTo(Packet('Mode', target=self.name, client=txt))
        else:
            self.server.SendTo(Packet('Mode', target=self.name))
    def txt_devoice(self, txt):
        self.server.SendTo(Packet('Devoice', target=self.name, client=txt))
    def txt_voice(self, txt):
        self.server.SendTo(Packet('Voice', target=self.name, client=txt))
    def txt_setmode(self, txt):
        parts=shlex.split(txt)
        if not self.CheckLen(parts, 2, 'a channel', 'a mode'):
            return
        try:
            mode=StrToMode(parts[1])
        except AttributeError:
            self.console.writeln(appconfig.get('STRS', 'UNREC')%{'object': 'mode enum'}, FgBgDict(appconfig.get('CLIENT', 'UNREC_FG'), appconfig.get('CLIENT', 'UNREC_BG')))
        else:
            if IsNick(parts[0]):
                self.server.SendTo(Packet('Mode', client=parts[0], set=mode))
            else:
                self.server.SendTo(Packet('Mode', target=parts[0], set=mode))
    def txt_unsetmode(self, txt):
        parts=shlex.split(txt)
        if not self.CheckLen(parts, 2, 'a channel', 'a mode'):
            return
        try:
            mode=StrToMode(parts[1])
        except AttributeError:
            self.console.writeln(appconfig.get('STRS', 'UNREC')%{'object': 'mode enum'}, FgBgDict(appconfig.get('CLIENT', 'UNREC_FG'), appconfig.get('CLIENT', 'UNREC_BG')))
        else:
            if IsNick(parts[0]):
                self.server.SendTo(Packet('Mode', client=parts[0], unset=mode))
            else:
                self.server.SendTo(Packet('Mode', target=parts[0], unset=mode))