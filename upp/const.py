'''
upp -- Unified Packet Protocol
const -- Library constants

Contains constants. Manipulate at your will, knowing that some of
these constants can compromise performance or stability!
'''

BUF_SIZE=32768 #The buffer size we are willing to read. Indirectly, the
#maximum length of a packet.

MAX_SESSIONS=256 #The default maximum number of sessions per channel. A
#greater demand will require more sessions, but too many can lead to
#massive memory usage. Too few can lead to DoS attacks.

class RSPERR: #RSP error codes; do not change
    OK=0 #No error (never sent over the wire)
    NOSERVICE=1 #The named service does not exist
    DENIED_ADDR=2 #Request denied based on remote address
    DENIED_SID=3 #Request denied based on stream identifier
    DENIED=4 #Request denied for other reason
    BADREQ=5 #Request not valid

class RSPLS: #RSP Listen States on sessions
    NONE=0 #Not expecting anything
    SYNC=1 #Expecting a Sync (or an Error)
    ACK=2 #Expecting an Ack or Close (or an Error)
    CLOSE=3 #Expecting a Close (and nothing else)

class SERV: #Service names (with versions)
    FPP='FPPv0.1'

FPP_CHUNK=1024 #The size of a pushed file chunk. This should be kept
#less than the size of an Ethernet frame on Ethernet networks (which
#is exactly 1500 counting header information), but is also efficiently
#implemented as a power of 2, thus making 1024 an obvious choice. You
#can play with this at runtime.

class BCSP: #BCSP operation codes
    NOP=0 #A keep-alive, more or less (also the default op for error packets)
    SYNC=1 #Synchronize connection
    TMIT=2 #Push data to peer
    ACK=3 #Acknowledge pushed data
    FIN=4 #Finish connection
    NO=5 #New Origin; the peer can not request data less than this index
    CMP=6 #CoMPression; use this compression method

class BCSPCMP: #BCSP compression methods
    NONE=0 #Uncompressed (least processing)
    BZIP2=1 #BZ2 (better)
    ZLIB=2 #ZLib (faster)

class BCSPERR: #BCSP error codes
    OK=0 #No error, operation is normal
    BADSVC=1 #Bad service identifier
    BADOP=2 #Bad operation
    BADCMP=3 #Bad compression
    SIDUSED=4 #Session identifier already in use
    SIDUNUSED=5 #Session identifier is not in use
    SVCLIM=6 #Too many connections to the service
    SVCDENY=7 #Connection rejected by software
    SEEKLIM=8 #Requested ACK seek out of bounds
    CMPERR=9 #Compression error
    CMPNOSUP=10 #Compression not supported
    ABORT=11 #Connection aborted by software
    #Error groups:
    TERMINATES_CONN=(BADSVC, SIDUSED, SVCLIM, SVCDENY, ABORT) #Errors that result in kick without ABORT

class BCSPS: #BCSP peer states
    NOTCON=0 #Not connected
    TRANSFERRING=1 #Transferring data
    CLOSING=2 #Closing connection

BCSP_CHUNK=1024 #The size of a BCSP data packet. See FPP_CHUNK above.
BCSP_DESLEAD=4096 #The desired transmission lead amount. The BCSP sender will attempt
#to be this many bytes ahead of the last ack it received. ceil(DESLEAD/CHUNK) is a good
#estimate as to how many chunks the sender will send on first connection.
BCSP_WAITTIME=1 #How many seconds to wait for an ack before sending any packets. This
#is ignored on the initial connection.