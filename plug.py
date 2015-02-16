'''
PIM4 -- Python Instant Messenger version 4
plug -- PIM Plugs

Implements plugs (the old PIM3 concept of an "extensible" tab).

One new flavor: GetPlugModules will get all modules starting with pl_
and return them as a list. The application can then extract a common
member (class Plug) and instantiate them as needed.

To prevent this autoloading, it is recommended a different prefix be
used...plx_?
'''

import os

class Plug(object):
    def __init__(self, app):
        self.app=app
        self.sock=app.sock
        self.app.AddPumpEntry(self.RecvPacket)
        self.allowentry=True
    def Discard(self):
        self.app.RemPumpEntry(self.RecvPacket)
    def SwitchTo(self):
        self.app.entry['state']=('normal' if self.allowentry else 'disabled')
    def SwitchFrom(self):
        pass
    def CreateFrame(self, tf):
        raise NotImplementedError('Plug must create a GUI!')
    def TFName(self):
        raise NotImplementedError('Plug must return frame name!')
    def RecvPacket(self, pkt, addr):
        print 'Plug', self.__class__.__name__, 'received', repr(pkt)
        getattr(self, 'cmd_'+pkt.cmd, self.OtherCmd)(pkt, addr)
    def OtherCmd(self, pkt, addr):
        pass
    def Take(self, txt):
        if txt.startswith('/'):
            head, sep, tail=txt[1:].partition(' ')
            getattr(self, 'txt_'+head, self.OtherTxt)(tail)
        else:
            self.NoncmdTxt(txt)
    def NoncmdTxt(self, txt):
        pass
    def OtherTxt(self, txt):
        pass

def GetPlugModules():
    mods=[]
    for i in os.listdir('.'):
        if i.startswith('pl_') and (i.endswith('.py') or i.endswith('.pyc')):
            mod=__import__(i.partition('.')[0])
            if mod not in mods:
                mods.append(mod)
    return mods