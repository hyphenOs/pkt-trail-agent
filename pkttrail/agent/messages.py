

from pkttrail.schema.messages import (
        PktTrailInitRequestSchema,
        PktTrailInitResponseSchema
    )

from .__version__ import sw_version, schema_version

class JSonRPCMessage:

    def __init__(self, method, version='2.0', id_=None):

        self._version = version
        self._method = method
        if id_ is not None:
            self._id_ = id_

class InitRequestMessage:

    def __init__(**kw):

        super().__init__(**kw)

        self._params = params


    def to_wire(self):
        message = PktTrailInitRequestMessage().load(self.__dict__)
