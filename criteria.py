'''
PIM4 -- Python Instant Messenger version 4
criteria -- Criteria management

Manages string-based criterion comparisons (like hostmasks).
'''

import fnmatch

def ApplyCriterion(client, criterion):
    if criterion.startswith('@'):
        return fnmatch.fnmatch(client.peer[0], criterion[1:])
    else:
        return fnmatch.fnmatch(client.nick, criterion)