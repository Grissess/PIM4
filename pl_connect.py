'''
PIM4 -- Python Instant Messenger version 4
pl_connect -- Connection Plug

Instantiates a connection to a PIM4 server.
'''

import socket
from Tkinter import *
import tkMessageBox

from plug import Plug
from plx_server import ServerPlug

from upp.packet import Packet

class ConnectPlug(Plug):
    __dispname__='Connect to PIM4'
    GUID=1
    @classmethod
    def GetName(cls):
        n=cls.GUID
        cls.GUID+=1
        return str(n)
    def __init__(self, app):
        Plug.__init__(self, app)
        self.name=self.GetName()
    def CreateFrame(self, tf):
        tf.Add(self.name, 'Connect')
        f=tf.frame[self.name]
        self.hostvar=StringVar(f, 'com.nexusg.org')
        self.lblhost=Label(f, text='Hostname:')
        self.lblhost.grid(row=0, column=0, sticky='nsew')
        self.hostent=Entry(f, textvariable=self.hostvar)
        self.hostent.grid(row=1, column=0, sticky='nsew')
        self.portvar=StringVar(f, '45903')
        self.lblport=Label(f, text='Port:')
        self.lblport.grid(row=2, column=0, sticky='nsew')
        self.portent=Entry(f, textvariable=self.portvar)
        self.portent.grid(row=3, column=0, sticky='nsew')
        self.nickvar=StringVar(f)
        self.lblnick=Label(f, text='Nickname:')
        self.lblnick.grid(row=4, column=0, sticky='nsew')
        self.nickent=Entry(f, textvariable=self.nickvar)
        self.nickent.grid(row=5, column=0, sticky='nsew')
        self.pwdvar=StringVar(f)
        self.lblpwd=Label(f, text='Password:')
        self.lblpwd.grid(row=6, column=0, sticky='nsew')
        self.pwdent=Entry(f, textvariable=self.pwdvar, show='*')
        self.pwdent.grid(row=7, column=0, sticky='nsew')
        self.usenoc2c=IntVar(f)
        self.usenoc2cchk=Checkbutton(f, text='Disable C2C (client-to-client)', variable=self.usenoc2c)
        self.usenoc2cchk.grid(row=8, column=0, sticky='nsew')
        self.usenosnd=IntVar(f)
        self.usenosndchk=Checkbutton(f, text='Disable sound', variable=self.usenosnd)
        self.usenosndchk.grid(row=9, column=0, sticky='nsew')
        self.btconnect=Button(f, text='Connect', command=self.Connect)
        self.btconnect.grid(row=10, column=0, sticky='nsew')
    def TFName(self):
        return self.name
    def Connect(self):
        host=self.hostvar.get()
        port=self.portvar.get()
        nick=self.nickvar.get()
        pwd=self.pwdvar.get()
        usenoc2c=self.usenoc2c.get()
        usenosnd=self.usenosnd.get()
        if not host:
            tkMessageBox.showerror('Missing Host', 'Please enter a hostname.')
            return
        if not port:
            tkMessageBox.showerror('Missing Port', 'Please enter a port number.')
            return
        if not nick:
            tkMessageBox.showerror('Missing Nick', 'Please enter a nick.')
            return
        try:
            port=int(port)
        except ValueError:
            tkMessageBox.showerror('Invalid Port', 'Please enter a numeric port.')
            return
        try:
            host=socket.gethostbyname(host)
        except socket.gaierror:
            tkMessageBox.showerror('Invalid Host', 'Could not resolve host. Please verify it was typed correctly.')
            return
        pkt=Packet('Sync', nick=nick)
        if pwd:
            pkt.password=pwd
        self.addr=(host, port)
        self.nick=nick
        self.pktbuf=[]
        self.sock.SendTo((host, port), pkt) #And now we wait...
    def cmd_Error(self, pkt, addr):
        if addr==self.addr:
            tkMessageBox.showerror('Server-sent Error', pkt.desc)
    def cmd_Sync(self, pkt, addr):
        print 'Got Sync from', addr
        if addr!=self.addr:
            print '...but it\'s not the right address. Abort...'
            return
        if pkt.result:
            sp=ServerPlug(self.app, self.addr, self.nick)
            self.app.AddPlug(sp)
            self.app.SetCurPlug(sp)
            for pkt in self.pktbuf:
                sp.RecvPacket(pkt, self.addr)
            self.app.RemPlug(self)
        else:
            s='Server failed to sync. Check parameters, and try again.\nThe server said:'
            for pkt in self.pktbuf:
                if not pkt.sonic:
                    s+='\n'+pkt.body
            tkMessageBox.showerror('Sync Error', s)
    def cmd_Msg(self, pkt, addr):
        if addr==self.addr:
            self.pktbuf.append(pkt)

ThisPlug=ConnectPlug            