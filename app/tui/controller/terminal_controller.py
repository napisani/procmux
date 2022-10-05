import os
import signal
import sys
from typing import List, Optional, TYPE_CHECKING

from ptterm import Terminal

from app.config import ProcMuxConfig
from app.log import logger
from app.tui.state.terminal_state import TerminalState
from app.tui.types import Process
from app.util.interpolation import interpolate, Interpolation

if TYPE_CHECKING:
    from app.tui.controller.tui_controller import TUIController


class TerminalController:
    def __init__(self,
                 controller: 'TUIController',
                 config: ProcMuxConfig,
                 process: Process
                 ):
        self._controller: TUIController = controller
        self._config: ProcMuxConfig = config
        self._terminal_state = TerminalState(process)

    @property
    def terminal(self) -> Optional[Terminal]:
        return self._terminal_state.terminal

    @property
    def is_running(self) -> bool:
        return self._terminal_state.is_running

    @property
    def _process(self) -> Process:
        return self._terminal_state.process

    def _export_env_vars(self) -> bool:
        if self._process.config.env:
            for key, value in self._process.config.env.items():
                os.environ[key] = value or ''
            return True
        return False

    def _adjust_path(self):
        proc_config = self._process.config
        if proc_config.add_path:
            if type(proc_config.add_path) == str:
                paths = [proc_config.add_path]
            paths = proc_config.add_path
            for p in paths:
                sys.path.append(p)

    def _change_working_directory(self):
        os.chdir(self._process.config.cwd)

    def _get_cmd(self, interpolations: Optional[List[Interpolation]] = None) -> List[str]:
        proc_config = self._process.config
        cmd = []
        if proc_config.shell:
            cmd.extend(self._config.shell_cmd)
            cmd.append(interpolate(proc_config.shell, interpolations))
        elif proc_config.cmd:
            cmd = [interpolate(c, interpolations) for c in proc_config.cmd]
        return cmd

    def stop_process(self):
        logger.info(f'in top process: {self._process.name}')
        if self.is_running and self.terminal:
            stop_signal = self._process.config.stop
            sig_code = getattr(signal, stop_signal)
            try:
                if hasattr(self.terminal.process.terminal, 'send_signal'):
                    logger.info(f'stopping process {self._process.name} with defined signal {stop_signal}')
                    self.terminal.process.terminal.send_signal(sig_code)
                else:
                    logger.info(
                        f'killing process {self._process.name} using x-platform process kill()'
                        f' - disregarding defined kill sig')
                    self._kill()
            except Exception as e:
                logger.error(f'failed to kill process: {self._process.name} {e}')

    def _kill(self):
        if self.is_running and self.terminal:
            try:
                logger.info(f'running kill() on process {self._process.name}')
                self.terminal.terminal_control.process.kill()
            except Exception as e:
                logger.error(f'failed to kill process name: {self._process.name} {e}')

    def _handle_process_done(self):
        logger.info(f'{self._process.name} is done')
        self._terminal_state.running = False
        self._controller.on_process_done(self._process)

    def _handle_process_spawned(self):
        logger.info(f'created terminal {self.terminal} for process {self._process.name}')
        self._terminal_state.running = True
        self._controller.on_process_spawned(self._process)

    def spawn_terminal(self, run_in_background: bool, interpolations: Optional[List[Interpolation]] = None):
        logger.info(f'in spawn terminal for process {self._process.name}')
        if self.is_running:
            logger.info(
                f'{self._process.name} terminal already running - returning existing terminal - {self.terminal}')
            return

        def before_exec():
            self._change_working_directory()
            self._export_env_vars()
            self._adjust_path()

        self._terminal_state.terminal = Terminal(command=self._get_cmd(interpolations),
                                                 width=self._config.style.width_100,
                                                 height=self._config.style.height_100,
                                                 style='class:terminal',
                                                 before_exec_func=before_exec,
                                                 done_callback=self._handle_process_done)
        if run_in_background:
            logger.info(f'rendering ptterm in the background, because {self._process.name} is not actively selected')
            if self.terminal:
                self.terminal.terminal_control.create_content(width=100, height=100)
        self._handle_process_spawned()

    def on_scroll_mode_change(self, scroll_mode: bool):
        if self.terminal and self._terminal_state.scroll_mode != scroll_mode:
            self._terminal_state.scroll_mode = scroll_mode
            if self._terminal_state.scroll_mode:
                self.terminal.enter_copy_mode()
            else:
                self.terminal.exit_copy_mode()
