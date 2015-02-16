'''
PIM4 -- Python Instant Messenger version 4
error -- Errors

Defines errors used by both client and server.
'''

class ERROR:
    NONE=600 #No error
    NOTFOUND=601 #Entity not found
    EXISTS=602 #Entity already exists
    ACCESS=603 #Generic access denied
    BANNED=604 #Banned from access
    DEVOICED=605 #Lacking voice access
    NOTEXT=606 #Lacking text access
    NOVOICE=607 #Lacking voice access
    NOTIN=608 #Entity not contained
    PROTOCOL=609 #A protocol rule was broken