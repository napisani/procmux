from __future__ import unicode_literals

from typing import Any, List

from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout import DynamicContainer, HSplit, ScrollbarMargin, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.dimension import D, Dimension
from prompt_toolkit.widgets import Frame

from app.tui.controller import ProcMuxController
from app.tui.keybindings import DocumentedKeybindings, register_app_wide_configured_keybindings, \
    register_configured_keybinding_no_event
from app.tui.state import FocusWidget


class SideBar:
    _right_padding: int = 5

    def __init__(self, controller: ProcMuxController):
        self._controller: ProcMuxController = controller
        self._fixed_width: int = self._controller.config.layout.processes_list_width

        self._filter_buffer: Buffer = Buffer(on_text_changed=self._controller.update_filter)
        buffer_input_keybindings = self._get_buffer_input_key_bindings()
        selection_keybindings = self._get_selection_key_bindings()
        self._buffer_control: BufferControl = BufferControl(
            buffer=self._filter_buffer,
            key_bindings=buffer_input_keybindings)
        self._list_control: FormattedTextControl = FormattedTextControl(
            text=self._get_text_fragments,
            show_cursor=False,
            focusable=True,
            key_bindings=selection_keybindings
        )

        self._controller.register_focusable_element(FocusWidget.SIDE_BAR_FILTER,
                                                    self._buffer_control,
                                                    buffer_input_keybindings.help_docs)
        self._controller.register_focusable_element(FocusWidget.SIDE_BAR_SELECT,
                                                    self._list_control,
                                                    selection_keybindings.help_docs)

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

    def _get_buffer_input_key_bindings(self):
        def on_exit_filter():
            self._controller.exit_filter(self._filter_buffer.text)

        kb = register_configured_keybinding_no_event(
            self._controller.config.keybinding.filter,
            on_exit_filter,
            DocumentedKeybindings(),
            'exit filter')
        return register_configured_keybinding_no_event(
            self._controller.config.keybinding.submit_filter,
            on_exit_filter,
            kb,
            'filter')

    def _get_selection_key_bindings(self):
        kb = register_configured_keybinding_no_event(self._controller.config.keybinding.up,
                                                     self._controller.sidebar_up,
                                                     DocumentedKeybindings(),
                                                     'up')
        kb = register_configured_keybinding_no_event(self._controller.config.keybinding.down,
                                                     self._controller.sidebar_down,
                                                     kb,
                                                     'down')

        def is_running():
            proc = self._controller.selected_process
            if not proc or not proc.running:
                return False
            return True

        kb = register_configured_keybinding_no_event(self._controller.config.keybinding.start,
                                                     self._controller.start_process,
                                                     kb,
                                                     'start',
                                                     should_show_help=lambda: not is_running())
        kb = register_configured_keybinding_no_event(self._controller.config.keybinding.stop,
                                                     self._controller.stop_process,
                                                     kb,
                                                     'stop',
                                                     should_show_help=is_running)
        kb = register_configured_keybinding_no_event(self._controller.config.keybinding.quit,
                                                     self._controller.quit,
                                                     kb,
                                                     'quit')

        def start_filter():
            self._filter_buffer.text = ''
            self._controller.start_filter()

        kb = register_configured_keybinding_no_event(self._controller.config.keybinding.filter,
                                                     start_filter,
                                                     kb,
                                                     'filter')
        kb = register_configured_keybinding_no_event(self._controller.config.keybinding.docs,
                                                     self._controller.view_docs,
                                                     kb,
                                                     'docs')
        kb = register_app_wide_configured_keybindings(self._controller.config,
                                                      self._controller.switch_focus,
                                                      self._controller.zoom,
                                                      self._controller.toggle_scroll,
                                                      kb)
        return kb

    def __pt_container__(self):
        return self._container
