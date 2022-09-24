from __future__ import unicode_literals

from prompt_toolkit.formatted_text import HTML, merge_formatted_text
from prompt_toolkit.layout import Window
from prompt_toolkit.layout.controls import FormattedTextControl

from app.context import ProcMuxContext


class ProcessDescriptionPanel:
    def __init__(self):
        self._ctx = ProcMuxContext()
        self.container = Window(
            height=1,
            content=FormattedTextControl(
                text=self._get_formatted_text,
                focusable=False,
                show_cursor=False
            ))

    def _get_formatted_text(self):
        idx = self._ctx.tui_state.selected_process_idx
        if idx < 0:
            return merge_formatted_text([HTML('')])
        name = self._ctx.tui_state.process_name_list[idx]
        desc = self._ctx.config.procs[name].description
        if not desc:
            desc = ''
        else:
            desc = " - " + desc
        result = [
            HTML(f'<b>{name}</b>{desc}')
        ]
        return merge_formatted_text(result)

    def __pt_container__(self):
        return self.container
