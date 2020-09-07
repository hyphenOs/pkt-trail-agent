"""
PktTrailAgent Class and associated functionality.
"""
from enum import Enum
from queue import Queue, Empty
import logging


_logger = logging.getLogger(__name__)
logging.basicConfig()


_default_config = {
        'keep_alive_interval' : 10,
        'event_get_timeout': 1

    }

class AgentStates(Enum):
    """An Enum of Agent States.

    At any given time, the Agent Class will be in one of these states.
    UNKNOWN: Usually occurs upon an unknown Error. Should never be reached
    OFFLINE: The default state when the agent class is created.
    INITIALIZING: Has contacted the Server but has not yet been acknowledged.
    INITIALIZED: Initialization Complete. Any additional Configuration
                 is received from the server.
    STARTED: Post initialization has informed the Server of Running
             information that has been acknowledged.
    ERROR: Internally defined Error condition. Should recover or restart
           if remains in this condition for some time.
    """
    UNKNOWN = -1
    OFFLINE = 0
    INITIALIZING = 1
    INITIALIZED = 2
    STARTED = 3
    CAPTURING = 4

    ANY = 5
    ANY_VALID = 6

    ERROR = 32


class AgentStateMachine:

    def __init__(self):
        self._states_dict = {}

    def add_action_for_event(self, state, action, event):
        pass

    def get_action_for_event(self, state, event):
        pass


class AgentEvents(Enum):
    """An enum of Agent Events

    """
    EV_STARTED = 0 #:
    EV_KEEPALIVE_EXPIRED = 1
    EV_INIT_RESPONSE = 2
    EV_INIT_FAILURE = 3


class PktTrailAgent:


    def __init__(self):
        self._state = AgentStates.OFFLINE
        self._state_machine = AgentStateMachine()
        self._event_queue = Queue()
        self._config = _default_config

    def init(self):

        self._add_default_actions()

    def run(self):
        """Fetches an Event from an Event Queue and performs corresponding
        action.

        """
        timeout = self._config.get('event_get_timeout', 1)

        while True:
            try:
                ev, args = self._event_queue.get(block=True, timeout=timeout)
            except Empty:
                ev = None

            if ev is None:
                # FIXME: Make it a logger.debug later on.
                _logger.warning("No Event found to process.")
                continue

            action = self._state_machine.get_action_for_event(self._state, ev)
            try:

                next_state = action(args)

                self._state = next_state

            except Exception as e:
                print(e)
                # FIXME: Need to see what needs to be done
                continue

    def _add_default_actions(self):
        agent_actions = [
                (AgentStates.OFFLINE, AgentEvents.EV_STARTED, self.send_init_msg),
                (AgentStates.INITIALIZING, AgentEvents.EV_INIT_RESPONSE, self.init_resp_received),
                (AgentStates.INITIALIZING, AgentEvents.EV_INIT_FAILURE, self.send_init_msg),
                (AgentStates.STARTED, AgentEvents.EV_KEEPALIVE_EXPIRED, self.send_keepalive_msg)
            ]

    def send_init_msg(self):
        """Sends init message and updates internal state based on result.

        If an error occurred during sending a message, increases the retries count with backoff.
        After certain retries hopelessly gives up.
        """
        return AgentStates.INITIALIZING


    def init_resp_received(self):
        """ Called when init response is received.

        Returns new state.
        """
        return AgentStates.INITIALIZED

    def send_keepalive_msg(self):
        """ Sends KeepAlive Message."""
        return AgentStates.STARTED


if __name__ == '__main__':
    agent = PktTrailAgent()
    agent.init()
    agent.run()

