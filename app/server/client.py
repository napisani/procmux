import http.client
import json
from urllib.parse import quote

from app.config import ProcMuxConfig


class SignalClient:

    def __init__(self, config: ProcMuxConfig):
        if not config.signal_server.enable:
            raise ValueError('Signal server is not enabled in config')
        if not config.signal_server.port:
            raise ValueError('Signal server port is not set in config')
        if not config.signal_server.host:
            raise ValueError('Signal server host is not set in config')

        self._base_url = config.signal_server.host
        self._port = config.signal_server.port

    def _get_error_message(self, response: http.client.HTTPResponse) -> str:
        body = response.read()
        body_json = json.loads(body.decode())
        if body_json.get('error'):
            return body_json['error']
        return body.decode()

    def restart_process(self, name: str):
        name = quote(name)
        conn = http.client.HTTPConnection(self._base_url, self._port)
        conn.request("POST", f"/restart-by-name/{name}")
        response = conn.getresponse()
        if response.status != 200:
            raise ValueError(
                f"Failed to restart process: {response.status} {self._get_error_message(response)}"
            )
        conn.close()

    def stop_process(self, name: str):
        name = quote(name)
        conn = http.client.HTTPConnection(self._base_url, self._port)
        conn.request("POST", f"/stop-by-name/{name}")
        response = conn.getresponse()
        if response.status != 200:
            raise ValueError(
                f"Failed to stop process: {response.status} {self._get_error_message(response)}"
            )
        conn.close()

    def restart_running_processes(self):
        conn = http.client.HTTPConnection(self._base_url, self._port)
        conn.request("POST", "/restart-running")
        response = conn.getresponse()
        if response.status != 200:
            raise ValueError(
                f"Failed to restart running processes: {response.status} {self._get_error_message(response)}"
            )
        conn.close()

    def stop_running_processes(self):
        conn = http.client.HTTPConnection(self._base_url, self._port)
        conn.request("POST", "/stop-running")
        response = conn.getresponse()
        if response.status != 200:
            raise ValueError(
                f"Failed to stop running processes: {response.status} {self._get_error_message(response)}"
            )
        conn.close()

    def start_process(self, name: str):
        name = quote(name)
        conn = http.client.HTTPConnection(self._base_url, self._port)
        conn.request("POST", f"/start-by-name/{name}")
        response = conn.getresponse()
        if response.status != 200:
            raise ValueError(
                f"Failed to start process: {response.status}  {self._get_error_message(response)}"
            )
        conn.close()

    def get_process_list(self):
        conn = http.client.HTTPConnection(self._base_url, self._port)
        conn.request("GET", "/")
        response = conn.getresponse()
        if response.status != 200:
            raise ValueError(
                f"Failed to get process list: {response.status} {self._get_error_message(response)}"
            )
        data = response.read()
        conn.close()
        return data
