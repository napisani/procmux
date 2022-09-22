from __future__ import unicode_literals

from typing import List

from prompt_toolkit.formatted_text import HTML, merge_formatted_text
from prompt_toolkit.layout import Window
from prompt_toolkit.layout.controls import FormattedTextControl

from app.context import ProcMuxContext
from app.tui_state import FocusWidget


class HelpPanel:
    def __init__(
            self
    ):
        self._ctx = ProcMuxContext()
        self.container = Window(
            height=1,
            # style='class:title',
            content=FormattedTextControl(
                text=self._get_formatted_text,
                focusable=False,
                show_cursor=False
            ))

    def _get_formatted_text(self):
        result = []
        delimiter = " | "
        key_config = self._ctx.config.keybinding
        if self._ctx.tui_state.focus == FocusWidget.SIDE_BAR:
            result.append(self._get_key_combo_text(key_config.up, 'up'))
            result.append(delimiter)
            result.append(self._get_key_combo_text(key_config.down, 'down'))
            result.append(delimiter)
            result.append(self._get_key_combo_text(key_config.start, 'start'))
            result.append(delimiter)
            result.append(self._get_key_combo_text(key_config.stop, 'stop'))
            result.append(delimiter)
            result.append(self._get_key_combo_text(key_config.quit, 'quit'))
            result.append(delimiter)
            result.append(self._get_key_combo_text(key_config.switch_focus, 'switch focus'))
        else:
            result.append(self._get_key_combo_text(key_config.switch_focus, 'switch focus'))
        return merge_formatted_text(result)

    def _get_key_combo_text(self, key_combos: List[str], label: str):
        [first, *_] = key_combos
        return HTML(f'<b>&lt;{first}&gt;</b> {label}')

    def __pt_container__(self):
        return self.container
