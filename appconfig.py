'''
PIM4 -- Python Instant Messenger version 4
appconfig -- Application Configuration

Handles retrieval of application configuration data.
'''

import ConfigParser

appcfg=ConfigParser.RawConfigParser()
appcfg.read('config.txt')

def get(section, option):
    return appcfg.get(section, option)