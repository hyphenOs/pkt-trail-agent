"""
PktTrailAgent Class and associated functionality.
"""
from enum import Enum
from queue import Queue, Empty
import logging
import threading

import requests

from .messages import (
        InitRequestMessage,
        KeepAliveRequestMessage
    )
from .messages import is_valid_response
from .utils import get_running_services

_logger = logging.getLogger(__name__)
logging.basicConfig()

class PktTrailAgentAPIError(Exception):
    pass

class PktTrailAgentInvalidAPIResponse(Exception):
    pass

_default_config = {
        'init_retry_timeout' : 5,
        'keepalive_interval' : 10,
        'max_keepalive_errors' : 5,
        'event_get_timeout': 1,
        'backoff_multiplier': 2,
        'max_backoff_secs': 10,
        'api_base_url': 'http://localhost:8000/agents/',
        'init_msg_path' : 'init/',
        'keepalive_msg_path': 'keepalive/'
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

    EV_INIT_RESPONSE = 1
    EV_INIT_FAILURE = 2

    EV_KEEPALIVE_EXPIRED = 3
    EV_KEEPALIVE_FAILURE = 4

class PktTrailAgent:
    """Main Agent Class."""

    def __init__(self):

        self._state = AgentStates.OFFLINE
        self._state_machine = AgentStateMachine()
        self._event_queue = Queue()
        self._config = _default_config

        self._init_errors = 0
        self._init_retry_timer = None

        self._keepalive_errors = 0
        self._keepalive_timer = None


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
                _logger.exception("Exception in run loop:")
                # FIXME: Need to see what needs to be done
                continue

    def _add_default_actions(self):
        agent_actions = [
                (AgentStates.OFFLINE, AgentEvents.EV_STARTED, self.send_init_req_msg),
                (AgentStates.INITIALIZING, AgentEvents.EV_INIT_RESPONSE, self.init_resp_received),
                (AgentStates.INITIALIZING, AgentEvents.EV_INIT_FAILURE, self.send_init_req_msg),
                (AgentStates.INITIALIZED, AgentEvents.EV_KEEPALIVE_EXPIRED, self.send_keepalive_msg),
                (AgentStates.STARTED, AgentEvents.EV_KEEPALIVE_EXPIRED, self.send_keepalive_msg),
                (AgentStates.STARTED, AgentEvents.EV_KEEPALIVE_FAILURE, self.send_init_req_msg)
            ]

        for state, ev, action in agent_actions:
            self._state_machine.add_action_for_event(state, action, ev)

    def send_init_req_msg(self, *args):
        """Sends init message and updates internal state based on result.

        If an error occurred during sending a message, increases the retries count with backoff.
        After certain retries hopelessly gives up.
        """

        # If we are about to be sending init message, there should be no 'active' init timer.
        # if that exists, it's a leak
        assert self._init_retry_timer == None

        try:
            init_req = InitRequestMessage().to_wire()

            base_url = self._config['api_base_url']
            url = base_url + self._config['init_msg_path']
            response = requests.post(url, json=init_req)

            response_json = response.json()
            if not response.ok:
                raise PktTrailAgentAPIError

            if not is_valid_response(response_json):
                raise PktTrailAgentInvalidAPIResponse

            self._init_errors = 0

            # Go ahead start a keep-alive timer
            keepalive_timeout = self._config['keepalive_interval']
            self._keepalive_timer = threading.Timer(keepalive_timeout, self._do_keepalive_interval)
            self._keepalive_timer.start()

            return AgentStates.INITIALIZED

        except Exception as e:
            _logger.exception("Exception:")
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

    def send_keepalive_msg(self, *args):
        """ Sends KeepAlive Message."""

        # If we are about to be sending keep-alive message, there should be no 'active'
        # keep-alive timer. If that exists, it's a leak
        assert self._keepalive_timer == None

        try:
            running_services = get_running_services()
            keepalive_req = KeepAliveRequestMessage(services=running_services).to_wire()

            base_url = self._config['api_base_url']
            url = base_url + self._config['keepalive_msg_path']
            response = requests.post(url, json=keepalive_req)

            response_json = response.json()
            if not response.ok:
                raise PktTrailAgentAPIError

            if not is_valid_response(response_json):
                raise PktTrailAgentInvalidAPIResponse

            self._keepalive_errors = 0
        except Exception as e:
            _logger.exception("Exception:")
            self._keepalive_errors += 1

            if self._keepalive_errors == self._config['max_keepalive_errors']:
                _logger.error("Maximum Keep Alive Errors Reached, Re-initializing.")

                ev = AgentEvents.EV_KEEPALIVE_FAILURE
                _logger.warning("Adding event (%s) to event queue.", ev)
                self._event_queue.put((ev, ()))

                return AgentStates.STARTED

        # Go ahead start a keep-alive timer
        keepalive_timeout = self._config['keepalive_interval']
        self._keepalive_timer = threading.Timer(keepalive_timeout, self._do_keepalive_interval)
        self._keepalive_timer.start()

        return AgentStates.STARTED


    def _do_init_retry_timeout(self):
        self._init_retry_timer = None

        ev = AgentEvents.EV_INIT_FAILURE
        _logger.warning("Adding event (%s) to event queue.", ev)
        self._event_queue.put((ev, ()))

    def _do_keepalive_interval(self):

        self._keepalive_timer = None

        ev = AgentEvents.EV_KEEPALIVE_EXPIRED
        _logger.warning("Adding event (%s) to event queue.", ev)
        self._event_queue.put((ev, ()))


    def __repr__(self):
        return "PktTrailAgent: State: {}, Pending Events: {}".format(
                self._state, self._event_queue.qsize())


if __name__ == '__main__':
    agent = PktTrailAgent()
    agent.init()
    agent.run()

