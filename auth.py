'''
PIM4 -- Python Instant Messenger version 4
auth -- Authentication

Handles authentication of clients. That is,:
-A client's authentication packet is checked against a database,
 possibly containing passwords. If this fails, authentication does not
 succeed.
-A client may be bestowed special privileges and modes, such as server
 op mode.
'''

import ConfigParser
import hashlib

from modes import MODE

CHARS_ALLOWED='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_'
AUTH_UNAME='.auth'

class Authorizer(object):
    def Authenticate(self, cli, pkt):
        raise NotImplementedError('Authenticator subclass must define .Authenticate()')

class IniFileAuth(Authorizer):
    def __init__(self, fname='auth.cfg'):
        self.conf=ConfigParser.RawConfigParser()
        self.conf.read(fname)
    def Authenticate(self, cli, pkt):
        for ch in cli.nick:
            if ch not in CHARS_ALLOWED:
                cli.Msg(AUTH_UNAME, '~', 'Illegal characters in nick. You are not authed.')
                return False
        if not self.conf.has_section(cli.nick):
            cli.Msg(AUTH_UNAME, '~', 'Welcome! You are not registered; please ask a server operator to register you. You have been authed.')
            return True
        else:
            cli.modes.Set(MODE.REGISTERED)
            cli.Msg(AUTH_UNAME, '~', 'Welcome! You are registered. Please wait while your credentials are checked...')
            if self.conf.has_option(cli.nick, 'password'):
                cli.Msg(AUTH_UNAME, '~', 'Password set...')
                if not hasattr(pkt, 'password'):
                    cli.Msg(AUTH_UNAME, '~', 'Please provide a password. You are not authed.')
                    return False
                if hashlib.sha512(pkt.password).hexdigest()!=self.conf.get(cli.nick, 'password'):
                    cli.Msg(AUTH_UNAME, '~', 'Password failed. You are not authed.')
                    return False
                else:
                    cli.Msg(AUTH_UNAME, '~', 'Password succeeded.')
            if self.conf.has_option(cli.nick, 'sop'):
                cli.modes.Set(MODE.SOP)
                cli.Msg(AUTH_UNAME, '~', 'You are a server operator. (Grissess says welcome :) .)')
                cli.Msg(AUTH_UNAME, '~', '(Please don\'t break me...)')
            cli.Msg(AUTH_UNAME, '~', 'Done. You are authed.')
            return True