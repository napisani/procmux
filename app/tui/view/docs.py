from typing import Callable, Union

from prompt_toolkit import HTML
from prompt_toolkit.formatted_text import merge_formatted_text
from prompt_toolkit.formatted_text.base import FormattedText
from prompt_toolkit.layout import FormattedTextControl, Window
from prompt_toolkit.widgets import Frame

from app.tui.types import FocusWidget
from app.tui.controller.tui_controller import TUIController


class DocsDialog:
    def __init__(self, controller: TUIController):
        self._controller: TUIController = controller
        self._container: Frame = Frame(
            title=self._get_title,
            body=Window(
                content=FormattedTextControl(
                    text=self._get_formatted_text,
                    focusable=True,
                    show_cursor=False
                )))
        self._controller.register_focusable_element(FocusWidget.DOCS, self._container)

    def _get_title(self) -> str:
        process = self._controller.selected_process
        return process.name if process else 'Help'

    def _get_formatted_text(self) -> Union[HTML, Callable[[], FormattedText]]:
        process = self._controller.selected_process
        if process:
            result = []
            if process.config.description:
                result.append(HTML(f'<b>{process.config.description}</b>\n'))
            if process.config.docs:
                result.append(HTML(process.config.docs))
            if len(result) == 0:
                result.append(f'No docs available for process: {process.name}')

            return merge_formatted_text(result)
        return HTML('No process is currently selected.')

    def __pt_container__(self):
        return self._container
