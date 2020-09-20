"""
PktTrailAgent Class and associated functionality.
"""
from enum import Enum
from queue import Queue, Empty
import logging
import threading

import requests

from .messages import InitRequestMessage

_logger = logging.getLogger(__name__)
logging.basicConfig()


_default_config = {
        'init_retry_timeout' : 5,
        'keep_alive_interval' : 10,
        'event_get_timeout': 1,
        'backoff_multiplier': 2,
        'max_backoff_secs': 10,
        'api_url': ''
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
        """Adds action to our internal 'states_dict' with keys as `(state, event)` tuple."""

        state_event = (state, event)
        _logger.warning("Adding action %s for Event: %s in state: %s",
                action, event, state)
        self._states_dict[state_event] = action

        _logger.warning("states dict: %s", self._states_dict)

    def get_action_for_event(self, state, event):
        return self._states_dict[(state, event)]


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

        self._init_errors = 0


    def init(self):

        self._add_default_actions()

        ev = AgentEvents.EV_STARTED
        self._event_queue.put((ev, ()))

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
            _logger.warning("performing action: %s", action)
            try:

                next_state = action(args)

                self._state = next_state

            except Exception as e:
                print(e)
                # FIXME: Need to see what needs to be done
                continue

    def _add_default_actions(self):
        agent_actions = [
                (AgentStates.OFFLINE, AgentEvents.EV_STARTED, self.send_init_req_msg),
                (AgentStates.INITIALIZING, AgentEvents.EV_INIT_RESPONSE, self.init_resp_received),
                (AgentStates.INITIALIZING, AgentEvents.EV_INIT_FAILURE, self.send_init_req_msg),
                (AgentStates.STARTED, AgentEvents.EV_KEEPALIVE_EXPIRED, self.send_keepalive_msg)
            ]

        for state, ev, action in agent_actions:
            self._state_machine.add_action_for_event(state, action, ev)

    def send_init_req_msg(self, *args):
        """Sends init message and updates internal state based on result.

        If an error occurred during sending a message, increases the retries count with backoff.
        After certain retries hopelessly gives up.
        """
        try:
            init_req = InitRequestMessage().to_wire()

            url = self._config.api_url
            response = requests.post(url, init_req)

            self._init_errors = 0
            return AgentStates.INITIALIZED

        except Exception as e:
            _logger.error("Exception:")
            self._init_errors += 1

            timeout = self._config['init_retry_timeout'] * self._init_errors
            if timeout > self._config['max_backoff_secs']:
                timeout = self._config['max_backoff_secs']
            _logger.warning("timeout: %d", timeout)

            self._init_retry_timer = threading.Timer(timeout, self._do_init_retry_timeout)
            self._init_retry_timer.start()

        return AgentStates.INITIALIZING


    def init_resp_received(self):
        """ Called when init response is received.

        Returns new state.
        """
        return AgentStates.INITIALIZED

    def send_keepalive_msg(self):
        """ Sends KeepAlive Message."""
        return AgentStates.STARTED


    def _do_init_retry_timeout(self):
        self._init_retry_timer = None

        ev = AgentEvents.EV_INIT_FAILURE
        _logger.warning("Adding event (%s) to event queue.", ev)
        self._event_queue.put((ev, ()))


    def __repr__(self):
        return "PktTrailAgent: State: {}, Pending Events: {}".format(
                self._state, self._event_queue.qsize())


if __name__ == '__main__':
    agent = PktTrailAgent()
    agent.init()
    agent.run()

