'''
PIM4 -- Python Instant Messenger version 4
multiframe -- Multiple Frame Managers

These (old) utilities present the tabbed (or listed) interface in the
PIM3. They're too damned useful to get rid of.

I changed the naming just a tad. It suits my usual CamelCase method
naming convention a bit better.
'''

from Tkinter import *

class TabFrame(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.button={}
        self.frame={}
        self.cur=None
        self.OnSwitch=lambda name: None
        self.cw()
    def cw(self):
        self.butframe=Frame(self, relief='ridge')
        self.butframe.grid(row=0, column=0, sticky='ew')
    def Add(self, name, label):
        if self.frame.has_key(name):
            print 'WARNING: TF DETECTED MULTIPLE ATTEMPT TO ADD; IGNORING...'
            return
        self.button[name]=Label(self.butframe, text=label)
        self.button[name].bind('<Enter>', self.EVEnterButton)
        self.button[name].bind('<Leave>', self.EVLeaveButton)
        self.button[name].bind('<1>', lambda ev, s=self, n=name: s.SwitchTo(n))
        self.button[name].pack(side='left')
        self.frame[name]=Frame(self, relief='raised', border=2, width=200, height=200)
    def Remove(self, name):
        if name==self.cur and hasattr(self.frame[name], 'OnSwitchedFrom'):
            self.frame[name].OnSwitchedFrom(None)
        self.button[name].destroy()
        self.frame[name].destroy()
        del self.button[name]
        del self.frame[name]
        names=self.button.keys()
        self.cur=None
        if names:
            self.SwitchTo(names[0])
    def SwitchTo(self, name):
        print 'TF: In SwitchTo..'
        self.button[name]['relief']='sunken'
        #This was injected for the PIM3's purpose
        self.button[name]['bg']='black'
        print 'TF: Performed style changes'
        if hasattr(self.frame[name], 'SwitchTo'):
            print 'SwitchTo called for frame', name
            self.frame[name].SwitchTo(self.cur)
        if self.cur:
            print self.cur, 'forgetting gridding'
            self.frame[self.cur].grid_forget()
            print self.cur, 'forgot gridding'
            if hasattr(self.frame[self.cur], 'SwitchFrom'):
                self.frame[self.cur].SwitchFrom(name)
                print 'SwitchFrom called for frame', name
            self.button[self.cur]['relief']='flat'
            print 'TF: Other style reset'
        self.cur=name
        print 'TF: Cur set'
        self.frame[name].grid(row=1, column=0, sticky='nsew')
        print 'TF: Frame gridded'
        self.OnSwitch(self.cur)
        print 'TF: Master switch called'
    def EVEnterButton(self, ev):
        ev.widget['relief']='raised'
    def EVLeaveButton(self, ev):
        if self.cur and ev.widget is self.button[self.cur]:
            ev.widget['relief']='sunken'
        else:
            ev.widget['relief']='flat'

class ListFrame(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack(fill='both', expand=1)
        self.frame={}
        self.lbcntnts=[]
        self.cur=None
        self.cw()
    def cw(self):
        self.lb=Listbox(self)
        self.lb.pack(side='left', fill='y', expand=1)
        self.lb.bind('<1>', self.EVSwitch)
        self.dispfr=Frame(self, height=200, width=200, relief='raised', border=2)
        self.dispfr.pack(side='right', fill='both', expand=1)
    def EVSwitch(self, ev):
        self.switchto(self.lb.get(self.lb.nearest(ev.y)))
    def SwitchTo(self, name):
        print 'Switching to', name
        print 'Current contents are', self.lbcntnts
        if self.cur:
            print 'Self.cur was', self.cur
            print 'The frame associated was', self.frame[self.cur], '(a', self.frame[self.cur].__class__, 'object)'
            print 'This frame\'s mapping status is', self.frame[self.cur].winfo_manager(), self.frame[self.cur].winfo_ismapped()
            self.frame[self.cur].pack_forget()
            print 'Unpacked old'
        self.frame[name].pack()
        print 'Packed new'
        self.cur=name
        print 'Cur set'
    def Add(self, name, lbl):
        self.frame[name]=Frame(self.dispfr)
        self.lb.insert('end', name)
        self.lbcntnts.append(name)
    def Remove(self, name):
        idx=self.lbcntnts.index(name)
        self.lb.delete(idx)
        del self.lbcntnts[idx]
        self.frame[name].destroy()
        del self.frame[name]
        if self.cur==name:
            if not self.lbcntnts:
                cur=None
            else:
                cur=None
                self.SwitchTo(self.lbcntnts[-1])