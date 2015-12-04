'''
PIM4 -- Python Instant Messenger version 4
channel -- Definition of the Channel

Defines the channel (a group of users able to multicast to each other).
'''

from modes import Modes, MappedModes, MODE
from error import ERROR

class Channel(object):
    def __init__(self, server, name, modes=None):
        self.server=server
        self.name=name
        self.modes=modes or Modes()
        self.ucmodes=MappedModes()
        self.clients=set()
    def AddClient(self, cli):
        self.clients.add(cli)
    def RemoveClient(self, cli):
        self.clients.discard(cli)
    def HasClient(self, cli):
        return cli in self.clients
    def ClientByNick(self, nick):
        for cli in self.clients:
            if cli.nick==nick:
                return cli
        return None
    def TestBanned(self, cli):
        return self.ucmodes.GetModes(cli).Check(MODE.BANNED)
    def TestInvited(self, cli):
        return self.ucmodes.GetModes(cli).Check(MODE.INVITE)
    def TestRegistered(self, cli):
        return cli.modes.Check(MODE.REGISTERED)
    def TestDevoiced(self, cli):
        return self.ucmodes.GetModes(cli).Check(MODE.DEVOICED)
    def TestOp(self, cli):
        return self.ucmodes.GetModes(cli).Check(MODE.OP)
    def TestHop(self, cli):
        return self.TestOp(cli) or self.ucmodes.GetModes(cli).Check(MODE.HOP)
    def CheckParams(self, pkt, *args):
        for arg in args:
            if not hasattr(pkt, arg):
                return False
        return True
    def Ban(self, cli, byname=True):
        if byname:
            self.ucmodes.Set(MODE.BANNED, cli.nick)
        else:
            self.ucmodes.Set(MODE.BANNED, '@'+cli.peer[0])
    def Unban(self, cli, byname=True):
        if byname:
            self.ucmodes.Unset(MODE.BANNED, cli.nick)
        else:
            self.ucmodes.Unset(MODE.BANNED, '@'+cli.peer[0])
    def Devoice(self, cli, byname=True):
        if byname:
            self.ucmodes.Set(MODE.DEVOICED, cli.nick)
        else:
            self.ucmodes.Set(MODE.DEVOICED, '@'+cli.peer[0])
    def Voice(self, cli, byname=True):
        if byname:
            self.ucmodes.Unset(MODE.DEVOICED, cli.nick)
        else:
            self.ucmodes.Unset(MODE.DEVOICED, '@'+cli.peer[0])
    def Op(self, cli, byname=True):
        if byname:
            self.ucmodes.Set(MODE.OP, cli.nick)
        else:
            self.ucmodes.Set(MODE.OP, '@'+cli.peer[0])
    def Deop(self, cli, byname=True):
        if byname:
            self.ucmodes.Unset(MODE.OP, cli.nick)
        else:
            self.ucmodes.Unset(MODE.OP, '@'+cli.peer[0])
    def Hop(self, cli, byname=True):
        if byname:
            self.ucmodes.Set(MODE.HOP, cli.nick)
        else:
            self.ucmodes.Set(MODE.HOP, '@'+cli.peer[0])
    def Dehop(self, cli, byname=True):
        if byname:
            self.ucmodes.Unset(MODE.HOP, cli.nick)
        else:
            self.ucmodes.Unset(MODE.HOP, '@'+cli.peer[0])
    def cmd_Join(self, cli, pkt):
        if not cli.IsSop():
            if self.TestBanned(cli):
                cli.Error(ERROR.BANNED, 'You are banned from this channel.')
                return
            if self.modes.Check(MODE.INVITE) and not self.TestInvited(cli):
                cli.Error(ERROR.ACCESS, 'You are not invited to this invite-only channel.')
                return
            if self.modes.Check(MODE.DEVOICED):
                self.Devoice(cli)
                cli.Packet('Devoice', source=self.name, target=self.name, client=cli.nick)
            if self.modes.Check(MODE.REGISTERED) and not self.TestRegistered(cli):
                cli.Error(ERROR.ACCESS, 'YOu must be registered to join this channel.')
                return
            if self.modes.Check(MODE.SOP):
                cli.Error(ERROR.ACCESS, 'You must be a server operator to join this channel.')
                return
        cli.Packet('Join', target=self.name)
        for cl in self.clients:
            cl.Packet('Join', source=cli.nick, target=self.name)
        self.AddClient(cli)
    def cmd_Part(self, cli, pkt):
        if not self.HasClient(cli):
            cli.Error(ERROR.NOTIN, 'You aren\'t in this channel.')
            #Safe to continue anyways
        self.RemoveClient(self)
        #Remove the UC modes we should
        for mode in MODE.UNSETONPART:
            self.ucmodes.Unset(mode, cli.nick)
        cli.Packet('Part', target=self.name)
        # If this was the last user and the channel isn't permanent, delete this channel.
        if (not self.clients) and not self.modes.Check(MODE.PERMANENT):
            self.server.RemoveChannel(self)
    def cmd_Msg(self, cli, pkt):
        if not cli.IsSop():
            if self.TestDevoiced(cli):
                cli.Error(ERROR.DEVOICED, 'You are devoiced.')
                return
        if not self.CheckParams(pkt, 'body', 'sonic'):
            cli.Error(ERROR.PROTOCOL, 'Malformed Msg packet.')
            return
        if pkt.sonic and self.modes.Check(MODE.NOSOUND):
            cli.Error(ERROR.NOVOICE, 'No sound allowed.')
            return
        if (not pkt.sonic) and self.modes.Check(MODE.NOTEXT):
            cli.Error(ERROR.NOTEXT, 'No text allowed.')
        for cl in self.clients:
            if cl==cli and not cli.modes.Check(MODE.ECHO):
                continue
            cl.Msg(cli.nick, self.name, pkt.body, pkt.sonic)
    cmd_Notice=cmd_Msg
    def cmd_Op(self, cli, pkt):
        if not cli.IsSop():
            if not self.HasClient(cli):
                cli.Error(ERROR.NOTIN, 'You aren\'t in this channel.')
                return
            if not self.TestOp(cli):
                cli.Error(ERROR.ACCESS, 'You must be op to use this command.')
                return
        if not self.CheckParams(pkt, 'client'):
            cli.Error(ERROR.PROTOCOL, 'Malformed Op packet.')
            return
        c=self.ClientByNick(pkt.client)
        if not c:
            cli.Error(ERROR.NOTFOUND, 'Client not found.')
            return
        self.Op(c)
        for cl in self.clients:
            cl.Packet('Op', source=cli.nick, target=self.name, client=pkt.client)
    def cmd_Deop(self, cli, pkt):
        if not cli.IsSop():
            if not self.HasClient(cli):
                cli.Error(ERROR.NOTIN, 'You aren\'t in this channel.')
                return
            if not self.TestOp(cli):
                cli.Error(ERROR.ACCESS, 'You must be op to use this command.')
                return
        if not self.CheckParams(pkt, 'client'):
            cli.Error(ERROR.PROTOCOL, 'Malformed Deop packet.')
            return
        c=self.ClientByNick(pkt.client)
        if not c:
            cli.Error(ERROR.NOTFOUND, 'Client not found.')
            return
        self.Deop(c)
        for cl in self.clients:
            cl.Packet('Deop', source=cli.nick, target=self.name, client=pkt.client)
    def cmd_Hop(self, cli, pkt):
        if not cli.IsSop():
            if not self.HasClient(cli):
                cli.Error(ERROR.NOTIN, 'You aren\'t in this channel.')
                return
            if not self.TestOp(cli):
                cli.Error(ERROR.ACCESS, 'You must be op to use this command.')
                return
        if not self.CheckParams(pkt, 'client'):
            cli.Error(ERROR.PROTOCOL, 'Malformed Hop packet.')
            return
        c=self.ClientByNick(pkt.client)
        if not c:
            cli.Error(ERROR.NOTFOUND, 'Client not found.')
            return
        self.Hop(c)
        for cl in self.clients:
            cl.Packet('Hop', source=cli.nick, target=self.name, client=pkt.client)
    def cmd_Dehop(self, cli, pkt):
        if not cli.IsSop():
            if not self.HasClient(cli):
                cli.Error(ERROR.NOTIN, 'You aren\'t in this channel.')
                return
            if not self.TestOp(cli):
                cli.Error(ERROR.ACCESS, 'You must be op to use this command.')
                return
        if not self.CheckParams(pkt, 'client'):
            cli.Error(ERROR.PROTOCOL, 'Malformed Dehop packet.')
        c=self.ClientByNick(pkt.client)
        if not c:
            cli.Error(ERROR.NOTFOUND, 'Client not found.')
            return
        self.Dehop(c)
        for cl in self.clients:
            cl.Packet('Dehop', source=cli.nick, target=self.name, client=pkt.client)
    def cmd_Kick(self, cli, pkt):
        if not cli.IsSop():
            if not self.HasClient(cli):
                cli.Error(ERROR.NOTIN, 'You aren\'t in this channel.')
                return
            if not self.TestHop(cli):
                cli.Error(ERROR.ACCESS, 'You must be hop to use this command.')
                return
        if not self.CheckParams(pkt, 'client'):
            cli.Error(ERROR.PROTOCOL, 'Malformed Kick packet.')
            return
        cl=self.ClientByNick(pkt.client)
        if not cl:
            cli.Error(ERROR.NOTFOUND, 'Cannot find client by that nick.')
            return
        if (not cli.IsSop()) and self.TestHop(cl):
            cli.Error(ERROR.ACCESS, 'Cannot kick other hops.')
            return
        self.RemoveClient(cl)
        cl.Packet('Part', target=self.name)
        for mode in MODE.UNSETONPART:
            self.ucmodes.Unset(mode, cli.nick)
        cl.Packet('Kick', source=cli.nick, target=self.name, client=cl.nick)
        for c in self.clients:
            c.Packet('Kick', source=cli.nick, target=self.name, client=cl.nick)
    def cmd_Ban(self, cli, pkt):
        if not cli.IsSop():
            if not self.HasClient(cli):
                cli.Error(ERROR.NOTIN, 'You aren\'t in this channel.')
                return
            if not self.TestHop(cli):
                cli.Error(ERROR.ACCESS, 'You must be hop to use this command.')
                return
        if not self.CheckParams(pkt, 'client'):
            cli.Error(ERROR.PROTOCOL, 'Malformed Ban packet.')
            return
        cl=self.ClientByNick(pkt.client)
        if not cl:
            cli.Error(ERROR.NOTFOUND, 'Cannot find client by that nick.')
            return
        if (not cli.IsSop()) and self.TestHop(cl):
            cli.Error(ERROR.ACCESS, 'Cannot ban other hops.')
            return
        self.Ban(cl)
        for c in self.clients:
            c.Packet('Ban', source=cli.nick, target=self.name, client=cl.nick)
    def cmd_Unban(self, cli, pkt):
        if not cli.IsSop():
            if not self.HasClient(cli):
                cli.Error(ERROR.NOTIN, 'You aren\'t in this channel.')
                return
            if not self.TestHop(cli):
                cli.Error(ERROR.ACCESS, 'You must be hop to use this command.')
                return
        if not self.CheckParams(pkt, 'client'):
            cli.Error(ERROR.PROTOCOL, 'Malformed Unban packet.')
            return
        if pkt.client not in self.ucmodes.map or not self.ucmodes.map[pkt.client].Check(MODE.BANNED):
            cli.Error(ERROR.NOTFOUND, 'Could not find banned client by that nick.')
            return
        self.ucmodes.Unset(MODE.BANNED, pkt.client)
        for c in self.clients:
            c.Packet('Unban', source=cli.nick, target=self.name, client=pkt.client)
    def cmd_Voice(self, cli, pkt):
        if not cli.IsSop():
            if not self.HasClient(cli):
                cli.Error(ERROR.NOTIN, 'You aren\'t in this channel.')
                return
            if not self.TestHop(cli):
                cli.Error(ERROR.ACCESS, 'You must be hop to use this command.')
                return
        if not self.CheckParams(pkt, 'client'):
            cli.Error(ERROR.PROTOCOL, 'Malformed Voice packet.')
            return
        cl=self.ClientByNick(pkt.client)
        if not cl:
            cli.Error(ERROR.NOTFOUND, 'Cannot find client by that nick.')
            return
        if (not cli.IsSop()) and self.TestHop(cl):
            cli.Error(ERROR.ACCESS, 'Cannot voice other hops.')
            return
        self.Voice(cl)
        for c in self.clients:
            c.Packet('Voice', source=cli.nick, target=self.name, client=cl.nick)
    def cmd_Devoice(self, cli, pkt):
        if not cli.IsSop():
            if not self.HasClient(cli):
                cli.Error(ERROR.NOTIN, 'You aren\'t in this channel.')
                return
            if not self.TestHop(cli):
                cli.Error(ERROR.ACCESS, 'You must be hop to use this command.')
                return
        if not self.CheckParams(pkt, 'client'):
            cli.Error(ERROR.PROTOCOL, 'Malformed Devoice packet.')
            return
        cl=self.ClientByNick(pkt.client)
        if not cl:
            cli.Error(ERROR.NOTFOUND, 'Cannot find client by that nick.')
            return
        if (not cli.IsSop()) and self.TestHop(cl):
            cli.Error(ERROR.ACCESS, 'Cannot devoice other hops.')
            return
        self.Devoice(cl)
        for c in self.clients:
            c.Packet('Devoice', source=cli.nick, target=self.name, client=cl.nick)
    def cmd_List(self, cli, pkt):
        cli.Packet('List', target=self.name, list=[cl.nick for cl in self.clients if not cl.modes.Check(MODE.SECRET)])
    def cmd_Mode(self, cli, pkt):
        if not (hasattr(pkt, 'set') or hasattr(pkt, 'unset')):
            if hasattr(pkt, 'client'):
                cl=self.ClientByNick(pkt.client)
                if not cl:
                    cli.Error(ERROR.NOTFOUND, 'Could not find client by that name.')
                    return
                cli.Packet('Mode', target=self.name, client=cl.nick, list=list(self.ucmodes.GetModes(cl)))
            else:
                cli.Packet('Mode', target=self.name, list=list(self.modes))
            return
        mode=(pkt.set if hasattr(pkt, 'set') else pkt.unset)
        if not cli.IsSop():
            if not self.HasClient(cli):
                cli.Error(ERROR.NOTIN, 'You aren\'t in this channel.')
                return
            if not self.TestHop(cli):
                cli.Error(ERROR.ACCESS, 'You must be hop to use this command.')
                return
            if mode in MODE.NEEDSOP:
                cli.Error(ERROR.ACCESS, 'You need to be a server op to use this command.')
                return
        if mode in MODE.NEEDOP and not self.TestOp(cli):
            cli.Error(ERROR.ACCESS, 'You need to be op to use this command.')
            return
        if hasattr(pkt, 'set'):
            self.modes.Set(mode)
            for cl in self.clients:
                cl.Packet('Mode', source=cli.nick, target=self.name, set=mode)
        else:
            self.modes.Unset(mode)
            for cl in self.clients:
                cl.Packet('Mode', source=cli.nick, target=self.name, unset=mode)
