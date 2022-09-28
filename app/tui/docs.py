from prompt_toolkit import HTML
from prompt_toolkit.formatted_text import merge_formatted_text
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import FormattedTextControl, Window
from prompt_toolkit.widgets import Frame

from app.context import ProcMuxContext
from app.log import logger
from app.tui_state import FocusWidget


class DocsDialog:
    def __init__(self, focus_manager):
        self._focus_manager = focus_manager

        self._ctx = ProcMuxContext()
        self._container = Frame(
            title=self._get_title,
            key_bindings=self._get_key_bindings(),
            body=Window(
                content=FormattedTextControl(
                    text=self._get_formatted_text,
                    focusable=True,
                    show_cursor=False
                )))
        self._focus_manager.register_focusable_element(FocusWidget.DOCS, self._container)

    def _get_key_bindings(self):
        kb = KeyBindings()

        for keybinding in self._ctx.config.keybinding.docs:
            @kb.add(keybinding)
            def _close_docs(_event) -> None:
                logger.info('in _close_docs')
                self._focus_manager.toggle_docs_open()
        return kb
    def _get_title(self):
        idx = self._ctx.tui_state.selected_process_idx
        if idx > -1:
            return self._ctx.tui_state.process_name_list[idx]
        return "Help"

    def _get_formatted_text(self):
        idx = self._ctx.tui_state.selected_process_idx
        if idx > -1:
            result = []
            proc_name = self._ctx.tui_state.process_name_list[idx]
            proc_config = self._ctx.config.procs[proc_name]
            if proc_config.description:
                result.append(HTML(f'<b>{proc_config.description}</b>\n'))
            if proc_config.docs:
                result.append(HTML(proc_config.docs))
            if len(result) == 0:
                result.append(f'No docs available for process: {proc_name}')

            return merge_formatted_text(result)
        return HTML("No process is currently selected.")

    def __pt_container__(self):
        return self._container
