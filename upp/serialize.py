'''
upp -- Unified Packet Protocol
serialize -- Serialization and Deserialization

Controls object (de)serialization.

Serializers (which also control deserialization) are registered
by deriving them from BaseSerializer. The metaclass will automatically
register any derivative classes, instantiating them once and using
that object to perform all serializations in this module. (Note that
outside code can also instantiate a serializer to achieve the same
effect.) Serializers derived this way must define __types__ as a tuple
(or, actually, any sequence) of types which the serializer supports.
Order is important; the most specific kind of serializer should come
first. (For the sake of user defined types and serializers, object
has no serializer, otherwise it would be a "catch-all".) Note that
some serializers do in fact work on multiple types, e.g. SequenceSerializer
will serialize both lists and tuples, but will return only a list. (If
a tuple is needed, it is assumed one can simply use tuple()). When
defined this way, serializers also receive a special attribute __idx__,
which is the index into the serializers list. This is used by module-level
functions Serialize and Deserialize (the __idx__ is prepended as a byte onto
the stream to identify what kind of data follows, kind of like a TLV).
Serializers are responsible for managing their own length. They will
recieve a file-like object, usually a StringIO, and are expected to
leave this pointing at the beginning of the next serialized object
in the stream, if it was successfully completed.

If you're emulating another type, e.g. you made a sequence type, feel
free to add your type to its __types__, e.g.
SequenceSerializer.__types__+=(MySequenceClass,). Take a look at the
code below to make sure your object supports everything it needs; e.g.
your object must be able to instantiate itself from a list and
support __iter__ in this example.
'''

import struct
import cStringIO

from const import *

SERIALIZERS=[]

class SerializerMeta(type):
    def __new__(mcs, name, bases, dict):
        tp=type.__new__(mcs, name, bases, dict)
        if name!='BaseSerializer':
            tp.__idx__=len(SERIALIZERS)
            SERIALIZERS.append(tp())
        return tp

class BaseSerializer(object):
    __metaclass__=SerializerMeta
    def Serialize(self, obj, f):
        raise NotImplementedError('Serializer must define .Serialize()')
    def Deserialize(self, f):
        raise NotImplementedError('Serializer must define .Deserialize()')

#And now, the moment you're all waiting for...basic serializers

class IntSerializer(BaseSerializer):
    __types__=(int,)
    def Serialize(self, obj, f):
        f.write(struct.pack('l', obj))
    def Deserialize(self, f):
        return struct.unpack('l', f.read(struct.calcsize('l')))[0]

class FloatSerializer(BaseSerializer):
    __types__=(float,)
    def Serialize(self, obj, f):
        f.write(struct.pack('d', obj))
    def Deserialize(self, f):
        return struct.unpack('d', f.read(struct.calcsize('d')))[0]

class StringSerializer(BaseSerializer):
    __types__=(str,)
    def Serialize(self, obj, f):
        f.write(struct.pack('L', len(obj))+obj)
    def Deserialize(self, f):
        l=struct.unpack('L', f.read(struct.calcsize('L')))[0]
        return f.read(l)

class LongSerializer(BaseSerializer):
    __types__=(long,)
    def Serialize(self, obj, f):
        f.write(struct.pack('L', len(str(obj)))+str(obj))
    def Deserialize(self, f):
        l=struct.unpack('L', f.read(struct.calcsize('L')))[0]
        return long(f.read(l))

class BoolSerializer(BaseSerializer):
    __types__=(bool,)
    def Serialize(self, obj, f):
        f.write(chr(1 if obj else 0))
    def Deserialize(self, f):
        return f.read(1)==chr(1)

class SequenceSerializer(BaseSerializer):
    __types__=(list, tuple)
    def Serialize(self, obj, f):
        f.write(struct.pack('L', len(obj)))
        for i in obj:
            s=Serialize(i)
            f.write(struct.pack('L', len(s))+s)
    def Deserialize(self, f):
        items=struct.unpack('L', f.read(struct.calcsize('L')))[0]
        ret=[]
        for i in xrange(items):
            l=struct.unpack('L', f.read(struct.calcsize('L')))[0]
            ret.append(Deserialize(f.read(l)))
        return ret

class MapSerializer(BaseSerializer):
    __types__=(dict,)
    def Serialize(self, obj, f):
        f.write(struct.pack('L', len(obj)))
        for k, v in obj.iteritems():
            pair=(k, v)
            s=Serialize(pair)
            f.write(struct.pack('L', len(s))+s)
    def Deserialize(self, f):
        items=struct.unpack('L', f.read(struct.calcsize('L')))[0]
        ret={}
        for i in xrange(items):
            l=struct.unpack('L', f.read(struct.calcsize('L')))[0]
            pair=Deserialize(f.read(l))
            ret[pair[0]]=pair[1]
        return ret

#Module-level functions

def Serialize(obj):
    sio=cStringIO.StringIO()
    for ser in SERIALIZERS:
        for tp in ser.__types__:
            if isinstance(obj, tp):
                sio.write(struct.pack('B', ser.__idx__))
                ser.Serialize(obj, sio)
                return sio.getvalue()
    raise TypeError('No serializers found for that type')

def Deserialize(s):
    sio=cStringIO.StringIO(s)
    idx=struct.unpack('B', sio.read(struct.calcsize('B')))[0]
    return SERIALIZERS[idx].Deserialize(sio)
