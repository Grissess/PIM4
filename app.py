'''
PIM4 -- Python Instant Messenger version 4
app -- Application

Defines the application.
'''

from Tkinter import *
import socket
import Queue

from upp.uppsocket import UPPSocket

from multiframe import TabFrame
from plug import GetPlugModules
from pump import PacketPump

class App(Frame):
    def __init__(self, master, **kwargs):
        Frame.__init__(self, master, **kwargs)
        self.option_readfile('tk_cfg.txt')
        self.sock=UPPSocket(socket.socket(socket.AF_INET, socket.SOCK_DGRAM))
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) #Oh hell, why not...
        self.sock.bind(('', 0))
        self.pump=PacketPump(self.sock)
        self.pump.SetEntry(self.RecvPacket)
        self.pump.Start()
        self.pktqueue=Queue.Queue(256)
        self.pktlisteners=set()
        self.plugs=set()
        self.curplug=None
        self.GenWidgets()
        self.PumpPackets()
    def GenWidgets(self):
        self.btadd=Button(self, text='Add...', command=self.BtAdd)
        self.btadd.grid(row=0, column=0, sticky='nsew')
        self.tf=TabFrame(self)
        self.tf.grid(row=1, column=0, sticky='nsew')
        self.tf.OnSwitch=self.TFSwitch
        self.entvar=StringVar(self)
        self.entry=Entry(self, textvariable=self.entvar)
        self.entry.bind('<KeyPress-Return>', self.EvEnter)
        self.entry.grid(row=2, column=0, sticky='ew')
    def SetCurPlug(self, plug):
        print 'APP: Set current plug', plug
        self.curplug=plug
        self.tf.SwitchTo(plug.TFName())
        print 'APP: Done switching'
    def TFSwitch(self, name):
        print 'APP: TFSwitch to', repr(name)
        print 'APP: Plugs are', self.plugs
        for plg in self.plugs:
            print 'PLG: TFName:', repr(plg.TFName()), '==', repr(name), 'is', plg.TFName()==name
            if plg.TFName()==name:
                self.curplug=plg
                return
        print 'APP: WARNING: TF switch did not correspond to plug, no switch occured...'
    def AddPlug(self, plug):
        print 'APP: Adding plug', plug
        self.plugs.add(plug)
        plug.CreateFrame(self.tf)
    def RemPlug(self, plug):
        print 'APP: Removing plug', plug
        self.plugs.discard(plug)
        plug.Discard()
        self.tf.Remove(plug.TFName())
        if plug is self.curplug:
            self.SetCurPlug(list(self.plugs)[0])
    def AlertPlug(self, plug):
        if self.curplug!=plug:
            self.tf.button[plug.TFName()]['bg']='#FF0000'
            self.bell()
    def RecvPacket(self, pkt, addr):
        self.pktqueue.put((pkt, addr))
        print 'RPKT:', pkt
    def PumpPackets(self):
        while not self.pktqueue.empty():
            pkt, addr=self.pktqueue.get()
            print 'PKT', repr(pkt)
            for listener in self.pktlisteners.copy():
                listener(pkt, addr)
        self.after(50, self.PumpPackets)
    def AddPumpEntry(self, entry):
        print 'APP: Adding entry', entry
        self.pktlisteners.add(entry)
    def RemPumpEntry(self, entry):
        print 'APP: Removing entry', entry
        self.pktlisteners.discard(entry)
    def EvEnter(self, ev):
        self.curplug.Take(self.entvar.get())
        self.entvar.set('')
    def BtAdd(self):
        taddplug=Toplevel()
        taddplug.title('Add Plug')
        waddplug=WAddPlug(taddplug, self)
        waddplug.pack(fill='both', expand=1)
    def destroy(self):
        print 'APP: Undergoing destruction'
        for plug in self.plugs:
            plug.Discard()
        print 'APP: Goodbye.'
        exit(0)

class WAddPlug(Frame):
    def __init__(self, master, app, **kwargs):
        Frame.__init__(self, master, **kwargs)
        self.app=app
        self.GenWidgets()
    def GenWidgets(self):
        self.buts=[]
        for i, plug in enumerate(GetPlugModules()):
            if hasattr(plug.ThisPlug, '__dispname__'):
                self.buts.append(Button(self, text=plug.ThisPlug.__dispname__, command=lambda plug=plug, self=self: self.CreatePlug(plug)))
                self.buts[-1].grid(row=i, column=0)
    def CreatePlug(self, plug):
        pl=plug.ThisPlug(self.app)
        self.app.AddPlug(pl)
        self.app.SetCurPlug(pl)
        self.winfo_toplevel().destroy()

if __name__=='__main__':
    root=Tk()
    root.title('PIM4 Client')
    app=App(root)
    app.pack(fill='both', expand=1)
    root.mainloop()