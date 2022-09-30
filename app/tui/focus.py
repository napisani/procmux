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

    def is_focused_on_free_form_input(self):
        return self.get_focused_widget() == FocusWidget.SIDE_BAR_FILTER

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

    def toggle_zoom(self):
        zoomed_in = self._ctx.tui_state.zoomed_in
        if zoomed_in:
            logger.info('setting zoomed_in to False')
            self._ctx.tui_state.zoomed_in = False
            self.focus_to_sidebar()
        else:
            success = self.focus_to_terminal()
            if success:
                logger.info('setting zoomed_in to True')
                self._ctx.tui_state.zoomed_in = True

    def toggle_docs_open(self):
        docs_open = self._ctx.tui_state.docs_open
        logger.info(f'setting docks_open to {not docs_open}')
        self._ctx.tui_state.docs_open = not docs_open
        if self._ctx.tui_state.docs_open:
            element = self.get_element_by_focus_widget(FocusWidget.DOCS)
            if element:
                self.set_focus(element)
        else:
            element = self.get_element_by_focus_widget(FocusWidget.SIDE_BAR_SELECT)
            if element:
                self.set_focus(element)

    def focus_to_terminal(self) -> bool:
        idx = self._ctx.tui_state.selected_process_idx
        if idx > -1:
            t_manager = self._ctx.tui_state.terminal_managers[idx]
            term = t_manager.get_terminal()
            if term:
                application = get_app()
                self._on_terminal_change(term)
                application.layout.focus(term)
                logger.info(f'focusing on terminal for idx: {idx} ')
                return True
        return False

    def toggle_sidebar_terminal_focus(self):
        assert self._on_terminal_change
        if self._ctx.tui_state.docs_open:
            logger.info('in toggle_sidebar_terminal_focus - but the docs are open, '
                        'toggling docs off instead')
            self.toggle_docs_open()
            return
        if self._ctx.tui_state.zoomed_in:
            logger.info('in toggle_sidebar_terminal_focus - currently zoomed in, '
                        'toggling zoom off instead')
            self.toggle_zoom()
            return
        idx = self._ctx.tui_state.selected_process_idx
        current_focus = self.get_focused_widget()
        if current_focus == FocusWidget.TERMINAL:
            self.focus_to_sidebar()
        elif current_focus == FocusWidget.SIDE_BAR_SELECT and idx is not None:
            self.focus_to_terminal()

    def focus_to_sidebar(self):
        logger.info('focusing on sidebar')
        side_bar = self.get_element_by_focus_widget(FocusWidget.SIDE_BAR_SELECT)
        if side_bar:
            application = get_app()
            application.layout.focus(side_bar)
