from __future__ import unicode_literals

from typing import Any, Callable, Optional

from prompt_toolkit.buffer import Buffer
from prompt_toolkit.formatted_text import HTML, merge_formatted_text
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, ScrollbarMargin, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.dimension import D, Dimension
from prompt_toolkit.widgets import Frame

from app.context import ProcMuxContext
from app.log import logger
from app.tui.focus import FocusManager


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
        self._fixed_width = self._ctx.config.layout.processes_list_width
        self._filter_buffer = Buffer()
        self.container = Frame(
            title='Processes',
            style='class:sidebar',
            width=D(min=self._fixed_width, max=self._fixed_width, weight=1),
            body=HSplit([
                # Window(content=BufferControl(buffer=self._filter_buffer, focusable=False)),
                Window(
                    content=FormattedTextControl(
                        text=self._get_formatted_text,
                        show_cursor=False,
                        focusable=True,
                        key_bindings=self._get_key_bindings(),
                    ),
                    style="class:select-box",
                    height=Dimension(min=5),
                    cursorline=True,
                    right_margins=[ScrollbarMargin(display_arrows=True), ],
                )
            ]))

    def _get_formatted_text(self):
        result = []
        for idx, name in enumerate(self._ctx.tui_state.process_name_list):
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

    def _get_key_bindings(self):
        kb = KeyBindings()
        for keybinding in self._ctx.config.keybinding.up:
            @kb.add(keybinding)
            def _go_up(_event) -> None:
                self._ctx.tui_state.selected_process_idx = (
                        (self._ctx.tui_state.selected_process_idx - 1) %
                        len(self._ctx.tui_state.process_name_list))
                if self._on_up:
                    self._on_up(self._ctx.tui_state.selected_process_idx)

        for keybinding in self._ctx.config.keybinding.down:
            @kb.add(keybinding)
            def _go_down(_event) -> None:
                self._ctx.tui_state.selected_process_idx = (
                        (self._ctx.tui_state.selected_process_idx + 1) %
                        len(self._ctx.tui_state.process_name_list))
                if self._on_down:
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
                for m in self._ctx.tui_state.terminal_managers:
                    m.send_kill_signal()
                if self._on_quit:
                    self._on_quit()
        return kb

    def __pt_container__(self):
        return self.container
