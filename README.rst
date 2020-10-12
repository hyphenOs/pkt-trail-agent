Getting Started
===============

This is a simple getting started guide for running the ``pkttrail`` agent. To
get started,

1. Install the dependencies using poetry install.

2. Start running the agent using following command -
   ``sudo <path-to-poetry> run python -m pkttrail.agent.agent``

This starts the ``agent``. If there is an error like -

.. code::

        Traceback (most recent call last):
          File "/home/gabhijit/Work/hyphenOs/pkt-trail-agent/pkttrail/agent/agent.py", line 190, in send_init_req_msg
            response = requests.post(url, json=init_req)
          File "/home/gabhijit/.cache/pypoetry/virtualenvs/pkt-trail-agent-u0rQj-Pd-py3.8/lib/python3.8/site-packages/requests/api.py", line 119, in post
            return request('post', url, data=data, json=json, **kwargs)
          File "/home/gabhijit/.cache/pypoetry/virtualenvs/pkt-trail-agent-u0rQj-Pd-py3.8/lib/python3.8/site-packages/requests/api.py", line 61, in request
            return session.request(method=method, url=url, **kwargs)
          File "/home/gabhijit/.cache/pypoetry/virtualenvs/pkt-trail-agent-u0rQj-Pd-py3.8/lib/python3.8/site-packages/requests/sessions.py", line 530, in request
            resp = self.send(prep, **send_kwargs)
          File "/home/gabhijit/.cache/pypoetry/virtualenvs/pkt-trail-agent-u0rQj-Pd-py3.8/lib/python3.8/site-packages/requests/sessions.py", line 643, in send
            r = adapter.send(request, **kwargs)
          File "/home/gabhijit/.cache/pypoetry/virtualenvs/pkt-trail-agent-u0rQj-Pd-py3.8/lib/python3.8/site-packages/requests/adapters.py", line 516, in send
            raise ConnectionError(e, request=request)
        requests.exceptions.ConnectionError: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /agents/init/ (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x7f09a3ca0040>: Failed to establish a new connection: [Errno 111] Connection refused'))
        WARNING:__main__:timeout: 10


Please make sure that the API Server is running. The source code for the API Server is available `here <https://github.com/hyphenOs/pkt-trail-fe-api-server.git>`_ .
