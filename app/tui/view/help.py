from __future__ import unicode_literals

from typing import Callable

from prompt_toolkit.formatted_text import FormattedText, HTML, merge_formatted_text
from prompt_toolkit.layout import Window
from prompt_toolkit.layout.controls import FormattedTextControl

from app.tui.types import KeybindingDocumentation
from app.tui.controller.tui_controller import TUIController


class HelpPanel:
    def __init__(self, controller: TUIController):
        self._controller: TUIController = controller
        self._container: Window = Window(
            height=1,
            content=FormattedTextControl(
                text=self._get_formatted_text,
                focusable=False,
                show_cursor=False
            ))

    def _get_formatted_text(self) -> Callable[[], FormattedText]:
        delimiter = " | "

        def intersperse(lst, item):
            full_list = [item] * (len(lst) * 2 - 1)
            full_list[0::2] = lst
            return full_list

        result = [self._get_key_combo_text(help_) for help_ in self._controller.get_app_keybindings().help_docs]
        if result:
            result = intersperse(result, delimiter)
        return merge_formatted_text(result)

    def _get_key_combo_text(self, help_doc: KeybindingDocumentation) -> HTML:
        return HTML(f'<b>&lt;{help_doc.help}&gt;</b> {help_doc.label}')

    def __pt_container__(self):
        return self._container
