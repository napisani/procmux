from __future__ import unicode_literals

from typing import List

from prompt_toolkit.formatted_text import HTML, merge_formatted_text
from prompt_toolkit.layout import Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.widgets import Frame

from app.context import ProcMuxContext
from app.tui.focus import FocusManager
from app.tui_state import FocusWidget


class HelpPanel:
    def __init__(
            self,
            focus_manager: FocusManager
    ):
        self._ctx = ProcMuxContext()
        self._focus_manager = focus_manager
        self.container = Window(
            height=1,
            content=FormattedTextControl(
                text=self._get_formatted_text,
                focusable=False,
                show_cursor=False
            ))

    def _get_formatted_text(self):
        result = []
        delimiter = " | "
        key_config = self._ctx.config.keybinding
        selected_process_running = self._ctx.tui_state.is_selected_process_running
        selected_process_has_terminal = self._ctx.tui_state.selected_process_has_terminal
        if self._focus_manager.get_focused_widget() == FocusWidget.SIDE_BAR_SELECT:
            result.append(self._get_key_combo_text(key_config.up, 'up'))
            result.append(delimiter)
            result.append(self._get_key_combo_text(key_config.down, 'down'))
            if not selected_process_running and not self._ctx.tui_state.quitting:
                result.append(delimiter)
                result.append(self._get_key_combo_text(key_config.start, 'start'))
            if selected_process_running:
                result.append(delimiter)
                result.append(self._get_key_combo_text(key_config.stop, 'stop'))
            result.append(delimiter)
            result.append(self._get_key_combo_text(key_config.quit, 'quit'))
            if selected_process_has_terminal:
                result.append(delimiter)
                result.append(self._get_key_combo_text(key_config.switch_focus, 'switch focus'))
                result.append(delimiter)
                result.append(self._get_key_combo_text(key_config.zoom, 'zoom'))
                result.append(delimiter)
                result.append(self._get_key_combo_text(key_config.toggle_scroll, 'toggle scroll'))
        elif self._focus_manager.get_focused_widget() == FocusWidget.SIDE_BAR_FILTER:
            result.append(self._get_key_combo_text(key_config.submit_filter, 'filter'))
        elif self._focus_manager.get_focused_widget() == FocusWidget.DOCS:
            result.append(self._get_key_combo_text(key_config.docs, 'docs'))
        else:
            result.append(self._get_key_combo_text(key_config.switch_focus, 'switch focus'))
            result.append(delimiter)
            result.append(self._get_key_combo_text(key_config.zoom, 'zoom'))
            result.append(delimiter)
            result.append(self._get_key_combo_text(key_config.toggle_scroll, 'toggle scroll'))
        return merge_formatted_text(result)

    def _get_key_combo_text(self, key_combos: List[str], label: str):
        [first, *_] = key_combos
        return HTML(f'<b>&lt;{first}&gt;</b> {label}')

    def __pt_container__(self):
        return self.container
