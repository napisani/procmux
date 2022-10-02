import os
import signal
import sys
from typing import List, Optional, Callable

from ptterm import Terminal

from app.config import ProcMuxConfig, ProcessConfig
from app.interpolation import interpolate, Interpolation
from app.log import logger


class TerminalManager:
    def __init__(self,
                 config: ProcMuxConfig,
                 process_config: ProcessConfig,
                 process_index: int,
                 process_name: str
                 ):
        self._config: ProcMuxConfig = config
        self._process_config: ProcessConfig = process_config
        self._process_index: int = process_index
        self._process_name: str = process_name
        self._on_process_spawned_handlers: List[Callable[[int], None]] = []
        self._on_process_done_handlers: List[Callable[[int], None]] = []
        self._running = False
        self._scroll_mode = False
        self._terminal: Optional[Terminal] = None

    @property
    def terminal(self) -> Optional[Terminal]:
        return self._terminal

    def _export_env_vars(self) -> bool:
        if self._process_config.env:
            for key, value in self._process_config.env.items():
                os.environ[key] = value or ''
            return True
        return False

    def _adjust_path(self):
        proc_config = self._process_config
        if proc_config.add_path:
            if type(proc_config.add_path) == str:
                paths = [proc_config.add_path]
            paths = proc_config.add_path
            for p in paths:
                sys.path.append(p)

    def _change_working_directory(self):
        os.chdir(self._process_config.cwd)

    def get_cmd(self, interpolations: Optional[List[Interpolation]] = None) -> List[str]:
        proc_config = self._process_config
        cmd = []
        if proc_config.shell:
            cmd.extend(self._config.shell_cmd)
            cmd.append(interpolate(proc_config.shell, interpolations))
        elif proc_config.cmd:
            cmd = [interpolate(c, interpolations) for c in proc_config.cmd]
        return cmd

    def is_running(self) -> bool:
        return self._terminal is not None and self._running

    def send_kill_signal(self):
        if self.is_running() and self._terminal:
            stop_signal = self._process_config.stop
            sig_code = getattr(signal, stop_signal)
            try:
                if hasattr(self._terminal.process.terminal, 'send_signal'):
                    logger.info(f'stopping process {self._process_name} with defined signal {stop_signal}')
                    self._terminal.process.terminal.send_signal(sig_code)
                else:
                    logger.info(
                        f'killing process {self._process_name} using x-platform process kill()'
                        f' - disregarding defined kill sig')
                    self.kill()
            except Exception as e:
                logger.error(f'failed to kill process: {self._process_name} {e}')

    def kill(self):
        if self.is_running() and self._terminal:
            try:
                logger.info(f'running kill() on process {self._process_name}')
                self._terminal.terminal_control.process.kill()
            except Exception as e:
                logger.error(f'failed to kill process name: {self._process_name} {e}')

    def _handle_process_done(self):
        logger.info(f'{self._process_name} is done')
        self._running = False
        for handler in self._on_process_done_handlers:
            handler(self._process_index)

    def _handle_process_spawned(self):
        logger.info(f'created terminal {self._terminal} for process {self._process_name}')
        self._running = True
        for handler in self._on_process_spawned_handlers:
            handler(self._process_index)

    def spawn_terminal(self, run_in_background: bool, interpolations: Optional[List[Interpolation]] = None):
        logger.info(f'in spawn terminal for process {self._process_name}')
        if self.is_running():
            logger.info(
                f'{self._process_name} terminal already running - returning existing terminal - {self._terminal}')
            return

        def before_exec():
            self._change_working_directory()
            self._export_env_vars()
            self._adjust_path()

        self._terminal = Terminal(command=self.get_cmd(interpolations),
                                  width=self._config.style.width_100,
                                  height=self._config.style.height_100,
                                  style='class:terminal',
                                  before_exec_func=before_exec,
                                  done_callback=self._handle_process_done)
        if run_in_background:
            logger.info(f'rendering ptterm in the background, because {self._process_name} is not actively selected')
            self._terminal.terminal_control.create_content(width=100, height=100)
        self._handle_process_spawned()

    def on_scroll_mode_change(self, process_index: int, scroll_mode: bool):
        if self._process_index == process_index and self._terminal and self._scroll_mode != scroll_mode:
            self._scroll_mode = scroll_mode
            if self._scroll_mode:
                self._terminal.enter_copy_mode()
            else:
                self._terminal.exit_copy_mode()

    def register_on_process_spawned_handler(self, handler: Callable[[int], None]):
        self._on_process_spawned_handlers.append(handler)

    def register_on_process_done_handler(self, handler: Callable[[int], None]):
        self._on_process_done_handlers.append(handler)
