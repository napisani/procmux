import os
import pty
import signal
import subprocess
import sys
from typing import Callable, List, Optional

from ptterm import Terminal

from app.config import ProcessConfig
from app.log import logger


class ProcessNotRunning(Exception):
    pass


class ProcessManager:

    def __init__(self, proc_config: ProcessConfig):
        self._proc_config = proc_config
        self._proc: subprocess.Popen = None

    def is_running(self) -> bool:
        if self._proc and self._proc.pid:
            if self._proc.returncode:
                return False
            return True
        return False

    def send_stop_signal(self):
        self._proc.send_signal(getattr(signal, self._proc_config.stop))

    def sync(self):
        if self.is_running():
            self._proc.communicate()
        else:
            raise ProcessNotRunning('a process that is not running cannot be synced')

    def start(self):
        kwargs = dict()
        if self._proc_config.env:
            kwargs['env'] = self._proc_config.env

        self._proc = subprocess.Popen(
            args=self._proc_config.shell,
            shell=(True if self._proc_config.shell else False),
            cwd=self._proc_config.cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            **kwargs
        )

    def start_pty(self):
        kwargs = dict()
        if self._proc_config.env:
            kwargs['env'] = self._proc_config.env
        r = pty.spawn(self._proc_config.shell, lambda fd: print(fd), lambda fd: '')
        print(r)


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

    def is_running(self):
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
