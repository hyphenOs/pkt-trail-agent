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
        JSON_RPC_VERSION_2,
        method_to_schema_class
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

    def __init__(self, agent_uuid, **kw):

        kw.update(
                method=OS_AGENT_INIT_MESSAGE,
                id_=str(uuid.uuid1()))

        super().__init__(**kw)

        self._params = {
                'schemaVersion' : schema_version,
                'agentSWVersion': sw_version,
                'agentUUID': agent_uuid
            }

    def to_wire(self):
        d = dict(jsonrpc=self._version,
                method=self._method,
                id=self._id,
                params=self._params)

        message = PktTrailInitRequestSchema().dump(d)

        return message


class KeepAliveRequestMessage(JsonRPCMessage):

    def __init__(self, agent_uuid, services=None, **kw):

        kw.update(
                method=OS_AGENT_KEEPALIVE_MESSAGE,
                id_=str(uuid.uuid1()))

        super().__init__(**kw)

        if services is None:
            services = []
        self._params = {
                'services':services,
                'agentUUID': agent_uuid}

    def to_wire(self):
        d = dict(jsonrpc=self._version,
                method=self._method,
                id=self._id,
                params=self._params)

        message = PktTrailKeepAliveRequestSchema().dump(d)

        return message


def is_valid_response(response_dict, msg_type):
    """Validates a given response.

    Get the schema for the response. If the Schema is obtained, try
    to `loads` the schema and upon exception return False. Else
    return True.
    """

    try:
        classes = method_to_schema_class[msg_type]
        schema = classes['response']
    except KeyError:
        _logger.exception("is_valid_response: type: %s", msg_type)
        return False

    try:
        _ = schema().load(response_dict)
    except Exception:
        _logger.exception("is_valid_response: validating Schema: %s", schema)
        return False

    return True


if __name__ == '__main__':

    import uuid
    agent_uuid = str(uuid.uuid1())
    i = InitRequestMessage(agent_uuid=agent_uuid)

    print(i.to_wire())
