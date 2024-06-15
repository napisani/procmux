import http.server
import json
import socketserver
import threading
from http import HTTPStatus
from time import sleep, time
from typing import Any, Callable, Dict, Optional, Tuple, Union
from urllib.parse import unquote

from app.config import ProcMuxConfig
from app.log import logger
from app.tui.controller.terminal_controller import TerminalController
from app.tui.state.process_state import ProcessState
from app.tui.types import Process

# Timeout (in seconds) for restarting a process
# maybe this can come from a query parameter later on
timeout = 5


def start_server(
    cfg: ProcMuxConfig,
    process_state: ProcessState,
    terminal_controllers: Dict[int, TerminalController],
    start_process_callback: Callable[[Process], None],
):

    active_httpd = None

    def _start_server():

        class SignalServer(http.server.SimpleHTTPRequestHandler):

            def __init__(self, request: bytes, client_address: Tuple[str, int],
                         server: socketserver.BaseServer):
                super().__init__(request, client_address, server)

            def log_error(self, _format: str, *args: Any) -> None:
                logger.error(*args)
                pass

            def log_request(self,
                            code: Union[str, int] = "-",
                            size: Union[str, int] = "-") -> None:
                logger.info(f"Request: {self.path} {code} {size}")

            def log_message(self, _format: str, *args: Any) -> None:
                logger.info.format(*args)

            def _send_ok(self, body: bytes):
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(body)

            def _send_error(self, code: int, message: str):
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": message}).encode())

            def _identify_process_by_name(self) -> Optional[Process]:
                name = self.path.split('/')[-1]
                name = unquote(name)
                for process in process_state.process_list:
                    if process.name == name:
                        return process
                return None

            def handle_get_process_list(self):
                process_list = [{
                    "name": p.name,
                    "running": p.running,
                    "index": p.index,
                    "scroll_mode": p.scroll_mode
                } for p in process_state.process_list]
                resp = json.dumps({"process_list": process_list}).encode()
                self._send_ok(bytes(resp))

            def handle_stop_by_name(self):
                process = self._identify_process_by_name()
                if process:
                    terminal_controller = terminal_controllers.get(
                        process.index)
                    if terminal_controller:
                        terminal_controller.stop_process()
                        self._send_ok(b'{}')
                        return
                self._send_error(HTTPStatus.NOT_FOUND, "Process not found")

            def handle_start_by_name(self):
                process = self._identify_process_by_name()
                if process:
                    if process.config.interpolations:
                        self._send_error(
                            HTTPStatus.BAD_REQUEST,
                            'Process requires interpolations, it cannot be remotely signaled to start'
                        )
                        return

                    start_process_callback(process)
                    self._send_ok(b'{}')
                    return
                self._send_error(HTTPStatus.NOT_FOUND, "Process not found")

            def _wait_for_process_stop(
                    self, terminal_controller: TerminalController):
                start_time = time()
                while terminal_controller.is_running:
                    if time() - start_time > timeout:
                        raise TimeoutError("Failed to stop process")
                    sleep(0.1)

            def handle_restart_by_name(self):
                process = self._identify_process_by_name()
                if process:
                    if process.config.interpolations:
                        self._send_error(
                            HTTPStatus.BAD_REQUEST,
                            'Process requires interpolations, it cannot be remotely signaled to start'
                        )

                    terminal_controller = terminal_controllers.get(
                        process.index)
                    if terminal_controller:
                        terminal_controller.stop_process()
                        try:
                            self._wait_for_process_stop(terminal_controller)
                        except TimeoutError:
                            self._send_error(HTTPStatus.INTERNAL_SERVER_ERROR,
                                             "Failed to stop process")
                            return
                        start_process_callback(process)
                        self._send_ok(b'{}')
                        return
                self._send_error(HTTPStatus.NOT_FOUND, "Process not found")

            def handle_restart_running(self):
                running_processes = [
                    p for p in process_state.process_list
                    if p.running and not p.config.interpolations
                ]
                for process in running_processes:
                    if process.running:
                        terminal_controller = terminal_controllers.get(
                            process.index)
                        if terminal_controller:
                            terminal_controller.stop_process()
                            try:
                                self._wait_for_process_stop(
                                    terminal_controller)
                            except TimeoutError:
                                self._send_error(
                                    HTTPStatus.INTERNAL_SERVER_ERROR,
                                    "Failed to stop process")
                                return
                            start_process_callback(process)
                self._send_ok(b'{}')

            def handle_stop_running(self):
                running_processes = [
                    p for p in process_state.process_list if p.running
                ]
                for process in running_processes:
                    terminal_controller = terminal_controllers.get(
                        process.index)
                    if terminal_controller:
                        terminal_controller.stop_process()
                self._send_ok(b'{}')

            def do_GET(self):
                if self.path == '/':
                    self.handle_get_process_list()
                else:
                    self._send_error(HTTPStatus.NOT_FOUND,
                                     "Endpoint not found")

            def do_POST(self):
                if self.path.startswith('/stop-by-name/'):
                    self.handle_stop_by_name()
                elif self.path.startswith('/start-by-name/'):
                    self.handle_start_by_name()
                elif self.path.startswith('/restart-by-name/'):
                    self.handle_restart_by_name()
                elif self.path.startswith('/restart-running'):
                    self.handle_restart_running()
                elif self.path.startswith('/stop-running'):
                    self.handle_stop_running()
                else:
                    self._send_error(HTTPStatus.NOT_FOUND,
                                     "Endpoint not found")

        with socketserver.TCPServer(
            (cfg.signal_server.host, cfg.signal_server.port),
                SignalServer) as httpd:
            nonlocal active_httpd
            active_httpd = httpd
            httpd.serve_forever()

    class ServerController:

        def __init__(self):
            self.thread = None

        def start(self):
            self.thread = threading.Thread(target=_start_server)
            self.thread.daemon = True
            self.thread.start()

        def stop(self):
            if active_httpd:
                active_httpd.shutdown()
            if self.thread:
                self.thread.join(5)

    controller = ServerController()
    controller.start()

    return controller
