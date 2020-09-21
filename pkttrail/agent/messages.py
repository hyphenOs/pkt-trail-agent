import uuid
import logging

from pkttrail.schema.messages import (
        PktTrailInitRequestSchema,
        PktTrailInitResponseSchema,

        PktTrailKeepAliveRequestSchema,
    )

from pkttrail.schema.messages import (
        OS_AGENT_INIT_MESSAGE,
        OS_AGENT_KEEPALIVE_MESSAGE,
        JSON_RPC_VERSION_2
    )

from .__version__ import sw_version, schema_version

_logger = logging.getLogger(__name__)

class JsonRPCMessage:

    def __init__(self, method, version=JSON_RPC_VERSION_2, id_=None):

        self._version = version
        self._method = method
        if id_ is not None:
            self._id = id_

class InitRequestMessage(JsonRPCMessage):

    def __init__(self, **kw):

        kw.update(
                method=OS_AGENT_INIT_MESSAGE,
                id_=str(uuid.uuid1()))

        super().__init__(**kw)

        self._params = {
                'schemaVersion' : schema_version,
                'agentSWVersion': sw_version
            }

    def to_wire(self):
        d = dict(jsonrpc=self._version,
                method=self._method,
                id=self._id,
                params=self._params)

        _logger.warning("Dict: %s", d)
        message = PktTrailInitRequestSchema().load(d)
        _logger.warning("message: %s", message)

        return message


class KeepAliveRequestMessage(JsonRPCMessage):

    def __init__(self, **kw):

        kw.update(
                method=OS_AGENT_KEEPALIVE_MESSAGE,
                id_=str(uuid.uuid1()))

        super().__init__(**kw)

        self._params = {}

    def to_wire(self):
        d = dict(jsonrpc=self._version,
                method=self._method,
                id=self._id,
                paams=self._params)

        _logger.warning("Dict: %s", d)
        message = PktTrailKeepAliveRequestSchema().load(d)
        _logger.warning("message: %s", message)

        return message


def is_valid_response(json):

    return True


if __name__ == '__main__':

    i = InitRequestMessage()

    print(i.to_wire())
