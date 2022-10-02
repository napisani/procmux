from __future__ import unicode_literals
from typing import Callable

from prompt_toolkit.formatted_text import HTML, merge_formatted_text
from prompt_toolkit.formatted_text.base import FormattedText
from prompt_toolkit.layout import Window
from prompt_toolkit.layout.controls import FormattedTextControl

from app.tui.controller import ProcMuxController


class ProcessDescriptionPanel:
    def __init__(self, controller: ProcMuxController):
        self._controller: ProcMuxController = controller
        self._container: Window = Window(
            height=1,
            content=FormattedTextControl(
                text=self._get_formatted_text,
                focusable=False,
                show_cursor=False
            ))

    def _get_formatted_text(self) -> Callable[[], FormattedText]:
        process = self._controller.selected_process
        if not process:
            return merge_formatted_text([HTML('')])
        desc = " - " + process.config.description if process.config.description else ''
        result = [HTML(f'<b>{process.name}</b>{desc}')]
        return merge_formatted_text(result)

    def __pt_container__(self):
        return self._container
