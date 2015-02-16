'''
PIM4 -- Python Instant Messenger version 4
modes -- Modes

Defines some mode sets.
'''

from criteria import ApplyCriterion

#Modes used by the system
#[U] indicates user modes,
#[C] indicates channel modes,
#[UC] indicates user-channel.
class MODE:
    SOP=1 #[U]Server operator [C]Only server operators can join
    REGISTERED=2 #[U]Registered to system [C]Only registered users can join
    BOT=3 #[U]User is a bot
    BANNED=4 #[UC]Banned from channel
    SILENT=5 #[C]No out-of-channel messaging [U]No user-user messaging
    DEVOICED=6 #[UC]User cannot send to channel [C]Auto-devoice all joining users
    OP=7 #[UC]User is operator on channel
    HOP=8 #[UC]User is half-op (can perform OP tasks, but cannot OP others)
    PERMANENT=9 #[C]Channel not removed when all part
    NOSOUND=10 #[C]Channel does not accept sonic data [U]User cannot accept sonic data (lacking equipment, etc.)
    NOTEXT=11 #[C]Channel does not accept text data
    PRETENDING=12 #[U]Server op is masquerading as regular user (for debugging)
    INVITE=13 #[C]Channel is invite-only, [UC]User is invited to channel
    ECHO=14 #[U]User wants to receive their own messages (for debugging)
    SECRET=15 #[C]Channel does not appear in List [U]User does not appear in List
    #--------------------------------------
    UNSETONPART=(DEVOICED, INVITE) #UC Modes unset from clients on part (by nick)
    NEEDSOP=(SOP, PERMANENT) #C Modes that require server op (SOP)
    NEEDOP=(INVITE, NOSOUND, NOTEXT, REGISTERED) #C Modes that require full op (not hop)
    UNEEDSOP=(SOP, REGISTERED, BOT, BANNED, DEVOICED, OP, HOP, PERMANENT,
              NOTEXT, INVITE) #U Modes that require server op

class Modes(set):
    def Set(self, mode):
        self.add(mode)
    def Unset(self, mode):
        self.discard(mode)
    def Check(self, mode):
        return mode in self

class MappedModes(object):
    def __init__(self):
        self.map={}
    def Set(self, mode, criterion):
        if criterion not in self.map:
            self.map[criterion]=Modes()
        self.map[criterion].Set(mode)
    def Unset(self, mode, criterion):
        if criterion not in self.map:
            self.map[criterion]=Modes()
        self.map[criterion].Unset(mode)
    def GetModes(self, client):
        modes=set()
        for criterion, mode in self.map.iteritems():
            if ApplyCriterion(client, criterion):
                modes.update(mode)
        return Modes(modes)