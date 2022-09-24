from typing import Callable

from prompt_toolkit.application import get_app

from app.context import ProcMuxContext
from app.log import logger
from app.tui_state import FocusWidget


class FocusManager:
    def __init__(self,
                 on_terminal_change: Callable):
        self._ctx = ProcMuxContext()
        self._focus_elements = []
        self._on_terminal_change = on_terminal_change

    def register_focusable_element(self, widget_type: FocusWidget, element):
        self._focus_elements.append((widget_type, element))

    def get_focused_widget(self) -> FocusWidget:
        application = get_app()
        for widget_type, element in self._focus_elements:
            if application.layout.has_focus(element):
                return widget_type
        return FocusWidget.TERMINAL

    def get_element_by_focus_widget(self, focus_widget: FocusWidget):
        items = [el for w, el in self._focus_elements if w == focus_widget]
        if items:
            return items[0]
        return None

    def set_focus(self, element):
        application = get_app()
        application.layout.focus(element)

    def toggle_sidebar_terminal_focus(self):
        assert self._on_terminal_change
        application = get_app()
        idx = self._ctx.tui_state.selected_process_idx
        current_focus = self.get_focused_widget()
        if current_focus == FocusWidget.TERMINAL:
            logger.info('focusing on sidebar')
            side_bar = self.get_element_by_focus_widget(FocusWidget.SIDE_BAR_SELECT)
            if side_bar:
                application.layout.focus(side_bar)
        elif current_focus == FocusWidget.SIDE_BAR_SELECT and idx is not None:
            t_manager = self._ctx.tui_state.terminal_managers[idx]
            term = t_manager.get_terminal()
            if term:
                self._on_terminal_change(term)
                application.layout.focus(term)
                logger.info(f'focusing on terminal for idx: {idx} ')
