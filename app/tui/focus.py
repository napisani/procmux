from typing import Callable

from prompt_toolkit.application import get_app

from app.context import ProcMuxContext
from app.log import logger
from app.tui_state import FocusWidget


class FocusManager:
    def __init__(self,
                 on_terminal_change: Callable):
        self._ctx = ProcMuxContext()
        self._side_bar = None
        self._on_terminal_change = on_terminal_change

    def register_side_bar(self, side_bar):
        self._side_bar = side_bar

    def get_focused_widget(self) -> FocusWidget:
        application = get_app()
        if application.layout.has_focus(self._side_bar):
            return FocusWidget.SIDE_BAR
        return FocusWidget.TERMINAL

    def set_focus(self, element):
        application = get_app()
        application.layout.focus(element)

    def toggle_sidebar_terminal_focus(self):
        assert self._side_bar
        assert self._on_terminal_change
        application = get_app()
        idx = self._ctx.tui_state.selected_process_idx
        if not application.layout.has_focus(self._side_bar):
            logger.info('focusing on sidebar')
            application.layout.focus(self._side_bar)
        elif idx is not None:
            t_manager = self._ctx.tui_state.terminal_managers[idx]
            term = t_manager.get_terminal()
            if term:
                self._on_terminal_change(term)
                application.layout.focus(term)
                logger.info(f'focusing on terminal for idx: {idx} ')
