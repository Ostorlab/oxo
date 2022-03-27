"""Agent health check mixin to ensure agents are operational.

The mixin runs a webservice by default on 0.0.0.0:5000 that must return 200 status and OK as a response.
The mixin enables adding multiple health check callbacks that must all return True.

Typical usage:

```python
    status_agent = agent_healthcheck_mixin.AgentHealthcheckMixin()
    status_agent.add_healthcheck(self._is_healthy)
    status_agent.start()
```
"""
import logging
from threading import Thread
from typing import Optional, Callable

import flask
from werkzeug import serving

logger = logging.getLogger(__name__)

DEFAULT_PORT = 5000
DEFAULT_HOST = '0.0.0.0'


class HealthcheckWebThread(Thread):
    """Webservice thread that return OK and NOK dependencies the health check return."""

    def __init__(self, name: str, host: str, port: int) -> None:
        """Setups a flask server.

        Args:
            name: name of the Flask service.
            host: host on which the web service is listening.
            port: port on which the web service is listening.
        """
        super().__init__()
        logger.info('Preparing flask')
        self._app = flask.Flask(name)
        self._server = serving.make_server(host=host, port=port, app=self._app, threaded=True)
        self._healthcheck_callbacks = []
        self._disable_verbose_logging()

    def _disable_verbose_logging(self):
        """Disable Flaskserver verbose logging."""
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

    def run(self) -> None:
        """Starts a long-running web service.

        Returns:
            None
        """
        logger.info('starting status server')
        self._server.serve_forever()

    def start(self) -> None:
        """Start thread in deamon mode.

        Returns:
            None
        """
        self._add_urls()
        self.daemon = True
        super().start()

    def stop(self) -> None:
        """Stop thread.

        Returns:
            None
        """
        self._server.shutdown()

    def _add_urls(self) -> None:
        """Add status URL at /stats."""
        self._app.add_url_rule('/status', 'status', self._status)

    def add_healthcheck(self, healthcheck_callback: Callable[[], bool]) -> None:
        """Add health check call back function that status will evaluate when called.

        Args:
            healthcheck_callback: Callback function, must take no argument and return a bool.

        Returns:
            None
        """
        logger.info('Adding healthcheck callback')
        self._healthcheck_callbacks.append(healthcheck_callback)

    def _status(self):
        """Healthcheck status endpoint.

        Returns:
            OK if all checks are work, NOK if not.
        """
        if all(healthcheck() for healthcheck in self._healthcheck_callbacks):
            logger.debug('Health checks status OK')
            return 'OK'
        else:
            logger.error('Health checks status NOK')
            return 'NOK'


class AgentHealthcheckMixin:
    """Agent heath check mixin exposing a pull-style health check function as a web endpoint.

    The endpoint is listing on http://0.0.0.0:5000/status and will return OK if all is good, and NOK in case one of the
    checks fail.

    **IMPORTANT**: the check might fail in a different way, for instance in case a check callback throws an exception,
    the web service intentionally do not catch them to make it easier to detect and debug. Health check should check
    for the presence of the OK and not the absence of NOK.
    """

    def __init__(self, name: Optional[str] = None, host=DEFAULT_HOST, port=DEFAULT_PORT) -> None:
        """Inits the health check web service thread and provides sane defaults.

        Args:
            name: name of the Flask service.
            host: host on which the web service is listening, defaults to 0.0.0.0.
            port: port on which the web service is listening, defaults to 5000.
        """
        self._healthcheck_web_thread = HealthcheckWebThread(name=(name or __name__), host=host, port=port)
        logger.debug('Starting healthcheck for agent.')

    def add_healthcheck(self, healthcheck_callback: Callable[[], bool]) -> None:
        """Add health check call back function that status will evaluate when called.

        Args:
            healthcheck_callback: Callback function, must take no argument and return a bool.

        Returns:
            None
        """
        logger.debug('enabling healthcheck')
        self._healthcheck_web_thread.add_healthcheck(healthcheck_callback)

    def start_healthcheck(self) -> None:
        """Start exposing the health service.

        Returns:
            None
        """
        self._healthcheck_web_thread.start()
        logger.debug('Healthcheck web thread started.')

    def stop_healthcheck(self) -> None:
        """Stop exposing the health service.

        Returns:
            None
        """
        self._healthcheck_web_thread.stop()
        logger.debug('Healthcheck web thread stopped.')
