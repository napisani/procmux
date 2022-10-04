from typing import Optional

from ptterm import Terminal

from app.tui.types import Process


class TerminalState:
    def __init__(self, process: Process):
        self.process = process
        self.running = False
        self.scroll_mode = False
        self.terminal: Optional[Terminal] = None

    @property
    def is_running(self) -> bool:
        return self.terminal is not None and self.running
