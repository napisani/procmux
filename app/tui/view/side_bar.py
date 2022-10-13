from __future__ import unicode_literals

from typing import Any, List

from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout import DynamicContainer, HSplit, ScrollbarMargin, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.dimension import D, Dimension
from prompt_toolkit.widgets import Frame

from app.tui.types import FocusWidget
from app.tui.controller.tui_controller import TUIController


class SideBar:
    _right_padding: int = 5

    def __init__(self, controller: TUIController):
        self._controller: TUIController = controller
        self._fixed_width: int = self._controller.config.layout.processes_list_width

        self._filter_buffer: Buffer = Buffer(on_text_changed=self._controller.update_filter)
        self._buffer_control: BufferControl = BufferControl(buffer=self._filter_buffer)
        self._list_control: FormattedTextControl = FormattedTextControl(
            text=self._get_text_fragments,
            show_cursor=False,
            focusable=True
        )

        self._controller.register_focusable_element(FocusWidget.SIDE_BAR_FILTER, self._buffer_control)
        self._controller.register_focusable_element(FocusWidget.SIDE_BAR_SELECT, self._list_control)
        self._controller.register_filter_change_handler(self.on_filter_change)

        def _get_filter_container() -> Window:
            if self._controller.filter_mode or self._filter_buffer.text:
                return Window(content=self._buffer_control,
                              height=D(min=1, max=1),
                              width=D(max=self._fixed_width - 1, weight=1))
            return Window(height=D(min=0, max=0),
                          width=D(max=self._fixed_width - 1, weight=1))

        self._container: Frame = Frame(
            title='Processes',
            style='class:sidebar',
            width=D(min=self._fixed_width, max=self._fixed_width, weight=1),
            body=HSplit([
                DynamicContainer(get_container=_get_filter_container),
                Window(
                    content=self._list_control,
                    style="class:select-box",
                    height=Dimension(min=5),
                    cursorline=True,
                    right_margins=[ScrollbarMargin(display_arrows=True), ],
                )
            ]))

    def on_filter_change(self, filter_text: str):
        if filter_text != self._filter_buffer.text:
            self._filter_buffer.text = filter_text

    def _get_text_fragments(self) -> List[Any]:
        result = []
        for process in self._controller.filtered_process_list:
            status = 'UP' if process.running else 'DOWN'
            status_fg = self._controller.config.style.status_running_color if process.running else \
                self._controller.config.style.status_stopped_color

            target_width = self._fixed_width - self._right_padding - len(status)
            name = process.name
            if len(name) > target_width:
                name = name[0:target_width - 3] + '...'
            name_fixed = f'%{target_width * -1}s' % name

            fg_color = self._controller.config.style.unselected_process_color
            bg_color = ''
            pointer_char = ' '

            if self._controller.is_selected_process(process):
                result.append(("[SetCursorPosition]", ""))
                bg_color = self._controller.config.style.selected_process_bg_color
                fg_color = self._controller.config.style.selected_process_color
                pointer_char = self._controller.config.style.pointer_char

            result.append((
                f'fg:{fg_color} bg:{bg_color} bold',
                f'{pointer_char}{name_fixed}',
                self._controller.on_sidebar_mouse_event
            ))
            result.append((f'fg:{status_fg} bg:{bg_color} bold', status, self._controller.on_sidebar_mouse_event))
            result.append(('', '\n', self._controller.on_sidebar_mouse_event))

        return result

    def __pt_container__(self):
        return self._container
