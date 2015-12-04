'''
PIM4 -- Python Instant Messenger version 4
plx_user -- User Plug

Hold my beer and watch this...
'''

from plx_channel import ChannelPlug
from util import WriteNick, FgBgDict
import appconfig

class UserPlug(ChannelPlug):
    def cmd_Msg(self, pkt, addr):
        if addr!=self.server.addr:
            return
        if pkt.source==self.name and pkt.target==self.server.nick and not pkt.sonic:
            WriteNick(self.console, pkt.source)
            self.console.writeln(pkt.body, FgBgDict(appconfig.get('MSGBODY', 'FG'), appconfig.get('MSGBODY', 'BG')))
            self.app.AlertPlug(self)
    def cmd_Notice(self, pkt, addr):
        if addr!=self.server.addr:
            return
        if pkt.target==self.server.nick and self.app.curplug is self and not pkt.sonic:
            WriteNick(self.console, pkt.source, True)
            self.console.writeln(pkt.body, FgBgDict(appconfig.get('NOTICEBODY', 'FG'), appconfig.get('NOTICEBODY', 'BG')))
            self.app.AlertPlug(self)
