from __future__ import unicode_literals

from typing import Any, Callable, Optional

from prompt_toolkit.application import get_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.formatted_text import HTML, merge_formatted_text
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import DynamicContainer, HSplit, ScrollbarMargin, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.dimension import D, Dimension
from prompt_toolkit.widgets import Frame

from app.context import ProcMuxContext
from app.log import logger
from app.tui.focus import FocusManager
from app.tui_state import FocusWidget


class SideBar:
    _right_padding = 5

    def __init__(
            self,
            focus_manager: FocusManager,
            on_start: Optional[Callable[[int], Any]] = None,
            on_stop: Optional[Callable[[int], Any]] = None,
            on_up: Optional[Callable[[int], Any]] = None,
            on_down: Optional[Callable[[int], Any]] = None,
            on_quit: Optional[Callable[[int], Any]] = None,
    ):
        self._focus_manager = focus_manager
        self._ctx = ProcMuxContext()
        self._on_start = on_start
        self._on_stop = on_stop
        self._on_up = on_up
        self._on_down = on_down
        self._on_quit = on_quit
        self._filter_mode = False
        self._fixed_width = self._ctx.config.layout.processes_list_width
        self._cached_proc_name_to_filtered_idx = ('',
                                                  {name: self._ctx.tui_state.get_process_index_by_name(name) for name in
                                                   self._ctx.tui_state.process_name_list})
        self._filter_buffer = Buffer()
        self._list_control = FormattedTextControl(
            text=self._get_formatted_text,
            show_cursor=False,
            focusable=True,
            key_bindings=self._get_selection_key_bindings(),
        )
        self._buffer_control = BufferControl(
            buffer=self._filter_buffer,
            key_bindings=self._get_buffer_input_key_bindings())

        self._focus_manager.register_focusable_element(FocusWidget.SIDE_BAR_FILTER, self._buffer_control)
        self._focus_manager.register_focusable_element(FocusWidget.SIDE_BAR_SELECT, self._list_control)

        def get_filter_container():
            if self._filter_mode or self._filter_buffer.text:
                return Window(content=self._buffer_control,
                              height=D(min=1, max=1),
                              width=D(max=self._fixed_width - 1, weight=1))
            return Window(height=D(min=0, max=0),
                          width=D(max=self._fixed_width - 1, weight=1))

        self.container = Frame(
            title='Processes',
            style='class:sidebar',
            width=D(min=self._fixed_width, max=self._fixed_width, weight=1),
            body=HSplit([
                DynamicContainer(get_container=get_filter_container),
                Window(
                    content=self._list_control,
                    style="class:select-box",
                    height=Dimension(min=5),
                    cursorline=True,
                    right_margins=[ScrollbarMargin(display_arrows=True), ],
                )
            ]))

    def _get_filtered_process_name_list(self):
        if not self._filter_buffer.text:
            return self._ctx.tui_state.process_name_list
        return [name for name in self._ctx.tui_state.process_name_list if
                name and self._filter_buffer.text.lower() in name.lower()]

    def get_filtered_index_for_process_name(self, proc_name) -> int:
        current_filter = ''
        if self._filter_buffer.text:
            current_filter = self._filter_buffer.text
        cache_key, proc_name_to_idx = self._cached_proc_name_to_filtered_idx
        if cache_key != current_filter:
            cache_key, proc_name_to_idx = (
                current_filter, {
                    name: idx for idx, name in enumerate(self._get_filtered_process_name_list())
                })
            self._cached_proc_name_to_filtered_idx = (cache_key, proc_name_to_idx)
        return proc_name_to_idx[proc_name]

    def _get_formatted_text(self):
        result = []
        for name in self._get_filtered_process_name_list():
            idx = self._ctx.tui_state.get_process_index_by_name(name)
            ctx = ProcMuxContext()
            manager = ctx.tui_state.terminal_managers[idx]
            status = "DOWN"
            status_fg = f'fg="{ctx.config.style.status_stopped_color}"'
            if manager.is_running():
                status = "UP"
                status_fg = f'fg="{ctx.config.style.status_running_color}"'

            target_width = self._fixed_width - self._right_padding - len(status)
            if len(name) > target_width:
                name = name[0:target_width - 3] + '...'
            name_fixed = f'%{target_width * -1}s' % name

            fg_color = f'fg="{ctx.config.style.unselected_process_color}"'
            bg_color = ''
            pointer_char = " "
            if idx == self._ctx.tui_state.selected_process_idx:
                result.append([("[SetCursorPosition]", "")])
                bg_color = f'bg="{ctx.config.style.selected_process_bg_color}"'
                fg_color = f'fg="{ctx.config.style.selected_process_color}"'
                pointer_char = "&#9654;"
            result.append(
                HTML(f'<style {fg_color} {bg_color}>'
                     f'<bold>{pointer_char}{name_fixed}</bold></style>'
                     f'<style {status_fg} {bg_color}>{status}</style>')
            )
            result.append("\n")

        return merge_formatted_text(result)

    def _get_buffer_input_key_bindings(self):
        kb = KeyBindings()
        for keybinding in self._ctx.config.keybinding.filter + self._ctx.config.keybinding.submit_filter:
            @kb.add(keybinding)
            def _exit_filter(_event) -> None:
                logger.info('in _exit_filter')
                self._ctx.tui_state.selected_process_idx = -1
                self._focus_manager.set_focus(self._list_control)
                self._filter_mode = False
        return kb

    def _get_selection_key_bindings(self):
        kb = KeyBindings()
        up = -1
        down = 1

        def move(direction: int) -> bool:
            tui_state = self._ctx.tui_state
            filtered_list = self._get_filtered_process_name_list()
            if not filtered_list:
                return False

            idx_in_main_list = self._ctx.tui_state.selected_process_idx
            if idx_in_main_list == -1:
                first_proc = filtered_list[0]
                tui_state.selected_process_idx = tui_state.get_process_index_by_name(first_proc)
                return True

            if len(filtered_list) < 2:
                return False

            name = self._ctx.tui_state.process_name_list[idx_in_main_list]
            idx_in_filtered_list = self.get_filtered_index_for_process_name(name)
            new_idx_in_filtered_list = ((idx_in_filtered_list + direction) % len(filtered_list))
            new_process_name = filtered_list[new_idx_in_filtered_list]
            self._ctx.tui_state.selected_process_idx = tui_state.get_process_index_by_name(new_process_name)
            return True

        for keybinding in self._ctx.config.keybinding.up:
            @kb.add(keybinding)
            def _go_up(_event) -> None:
                moved = move(up)
                if moved and self._on_up:
                    self._on_up(self._ctx.tui_state.selected_process_idx)

        for keybinding in self._ctx.config.keybinding.down:
            @kb.add(keybinding)
            def _go_down(_event) -> None:
                moved = move(down)
                if moved and self._on_down:
                    self._on_down(self._ctx.tui_state.selected_process_idx)

        for keybinding in self._ctx.config.keybinding.start:
            @kb.add(keybinding)
            def _start(_event) -> None:
                logger.info('in _start')
                if self._on_start:
                    self._on_start(self._ctx.tui_state.selected_process_idx)
        for keybinding in self._ctx.config.keybinding.stop:
            @kb.add(keybinding)
            def _stop(_event) -> None:
                logger.info('in _stop')
                if self._on_stop:
                    self._on_stop(self._ctx.tui_state.selected_process_idx)

        for keybinding in self._ctx.config.keybinding.quit:
            @kb.add(keybinding)
            def _quit(_event) -> None:
                logger.info('in _quit')
                for m in self._ctx.tui_state.terminal_managers:
                    m.send_kill_signal()
                if self._on_quit:
                    self._on_quit()
        for keybinding in self._ctx.config.keybinding.filter:
            @kb.add(keybinding)
            def _filter(_event) -> None:
                logger.info('in _filter')
                self._filter_mode = True
                self._filter_buffer.text = ''
                app = get_app()
                app.invalidate()
                self._ctx.tui_state.selected_process_idx = -1
                self._focus_manager.set_focus(self._buffer_control)

        return kb

    def __pt_container__(self):
        return self.container
