'''
PIM4 -- Python Instant Messenger version 4
tkconsole -- Tkinter Text-compatible console

An old PIM relic :)
'''

from Tkinter import *

import appconfig

STDWIDTH=80
STDHEIGHT=25

class Console(Text):
    def __init__(self, master=None, **cnf):
##        print ''
##        print 'Initializing Console...'
        Text.__init__(self, master, **cnf)
        self.guid=1
##        self.flashtags=[]
##        print 'Pre-flashon...'
##        self.flashon()
    fmt={'background': appconfig.get('CON_DEFAULT', 'BG'),
         'foreground': appconfig.get('CON_DEFAULT', 'FG'),
         'font': (appconfig.get('CON_DEFAULT', 'FONTFACE'), appconfig.get('CON_DEFAULT', 'FONTSIZE')),
         'flash': False}
    def write(self, txt, format=None):
        if not format:
            format=self.fmt
        else:
            for k, v in self.fmt.iteritems():
                format.setdefault(k, v)
##        if format['flash']:
##            self.flashtags.append('CONSOLE_TAG_'+str(self.guid))
        if 'flash' in format:
            del format['flash']
        self.tag_config('CONSOLE_TAG_'+str(self.guid), **format)
        self.insert('end', txt, ('CONSOLE_TAG_'+str(self.guid),))
        self.see('end')
        self.guid+=1
    def writeln(self, txt, format):
        self.write(txt+'\n', format)
    def w(self, txt, **f):
        self.writeln(txt, f)
    def clear(self):
        self.delete('0.0', 'end')
        self.guid=1 #Clears formatting, too.
##        self.flashtags=[]
##    def flashon(self):
##        print 'flashon>Importing thread...'
##        import thread
##        self._flashon=True
##        print 'flashon>Starting thread...'
##        print 'Thread has TID:', thread.start_new(self._flasher, (), {})
##    def flashoff(self):
##        self._flashon=False
##    def _flasher(self):
##        import time
##        print 'flasher>First call'
##        while self._flashon:
##            for i in self.flashtags:
##                fg=self.tag_cget(i, 'foreground')
##                bg=self.tag_cget(i, 'background')
##                self.tag_config(i, background=fg, foreground=bg)
##            self.update_idletasks()
##            time.sleep(0.5)