import os
import signal
import sys
from typing import Callable, List, Optional

from ptterm import Terminal

from app.log import logger


class TerminalManager:
    def __init__(
            self,
            process_name: str,
            terminal_ctor: Callable[[List[str]], Terminal],
            on_done: Optional[Callable] = None,
            on_spawn: Optional[Callable] = None
    ):
        from app.context import ProcMuxContext
        self._ctx = ProcMuxContext()
        self._term_ctor = terminal_ctor
        self._proc_name = process_name
        self._terminal: Terminal = None
        self._running = False
        self._on_done_callbacks = []
        if on_done:
            self._on_done_callbacks = [on_done]

        self._on_spawn_callbacks = []
        if on_spawn:
            self._on_spawn_callbacks = [on_spawn]

    def _export_env_vars(self) -> bool:
        proc_config = self._ctx.config.procs[self._proc_name]
        if proc_config.env:
            for key, value in proc_config.env.items():
                os.environ[key] = value
            return True
        return False

    def _adjust_path(self):
        proc_config = self._ctx.config.procs[self._proc_name]
        if proc_config.add_path:
            paths = proc_config.add_path
            if type(proc_config.add_path) == str:
                paths = [proc_config.add_path]
            for p in paths:
                sys.path.append(p)

    def _change_working_directory(self):
        proc_config = self._ctx.config.procs[self._proc_name]
        if proc_config.cwd:
            os.chdir(proc_config.cwd)

    def get_cmd(self) -> List[str]:
        proc_config = self._ctx.config.procs[self._proc_name]
        shell_cmd = self._ctx.config.shell_cmd
        cmd = []
        if proc_config.shell:
            cmd.extend(shell_cmd)
            cmd.append(proc_config.shell)
        else:
            cmd = proc_config.cmd
        return cmd

    def is_running(self) -> bool:
        return self._terminal and self._running

    def send_kill_signal(self):
        if self.is_running():
            stop_signal = self._ctx.config.procs[self._proc_name].stop
            sig_code = getattr(signal, stop_signal)
            try:
                if hasattr(self._terminal.process.terminal, 'send_signal'):
                    logger.info(f'stopping process with defined signal {stop_signal}')
                    self._terminal.process.terminal.send_signal(sig_code)
                else:
                    logger.info(f'using x-platform process kill() - disregarding defined kill sig')
                    self.kill()
            except Exception as e:
                logger.error(f'failed to kill process name: {self._proc_name} {e}')

    def kill(self):
        if self.is_running():
            try:
                logger.info('running kill()')
                self._terminal.terminal_control.process.kill()
            except Exception as e:
                logger.error(f'failed to kill process name: {self._proc_name} {e}')

    def _handle_process_done(self):
        logger.info(f'{self._proc_name} is done')
        self._running = False
        for handler in self._on_done_callbacks:
            handler()

    def spawn_terminal(self):
        if self.is_running():
            logger.info(f'spawned - returning existing terminal - {self._terminal}')
            return self._terminal

        def before_exec():
            self._change_working_directory()
            self._export_env_vars()
            self._adjust_path()

        self._terminal = self._term_ctor(self.get_cmd(), before_exec, self._handle_process_done)
        logger.info(f'created terminal {self._terminal}')
        self._running = True
        return self._terminal

    def get_terminal(self):
        return self._terminal

    def register_process_done_handler(self, on_done: Callable):
        self._on_done_callbacks.append(on_done)

    def register_process_spawn_handler(self, on_spawn: Callable):
        self._on_spawn_callbacks.append(on_spawn)

    def autostart_conditionally(self) -> bool:
        proc_config = self._ctx.config.procs[self._proc_name]
        if proc_config.autostart:
            logger.info(f'autostarting {self._proc_name}')
            self.spawn_terminal()
            return True
        return False
