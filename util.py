'''
PIM4 -- Python Instant Messenger version 4
util -- Occassional Utilities

You know, stuff used less often than it should be.
'''

import appconfig
from modes import MODE
from error import ERROR

def IsNick(txt):
    return not IsChannel(txt)

def IsChannel(txt):
    return txt[0] in '#&'

def FgBgDict(fg, bg):
    return {'foreground': fg, 'background': bg}

def WriteNick(con, nick, notice=False):
    con.write(('-' if notice else '<'), FgBgDict(appconfig.get('NICK', 'PUNCT_FG'), appconfig.get('NICK', 'PUNCT_BG')))
    if nick.startswith('.'):
        con.write(nick, FgBgDict(appconfig.get('NICK', 'SERVER_FG'), appconfig.get('NICK', 'SERVER_BG')))
    else:
        con.write(nick, FgBgDict(appconfig.get('NICK', 'FG'), appconfig.get('NICK', 'BG')))
    con.write(('- ' if notice else '> '), FgBgDict(appconfig.get('NICK', 'PUNCT_FG'), appconfig.get('NICK', 'PUNCT_BG')))

MODENUMTONAME=dict(zip(MODE.__dict__.values(), MODE.__dict__.keys()))
ERRNUMTONAME=dict(zip(ERROR.__dict__.values(), ERROR.__dict__.keys()))

def PrettyMode(mode):
    return str(mode)+' (MODE.'+MODENUMTONAME[mode]+')'

def PrettyError(err):
    return 'ERROR.'+ERRNUMTONAME[err]

def StrToMode(s):
    if s.startswith('MODE.'):
        s=s[5:]
    return getattr(MODE, s)