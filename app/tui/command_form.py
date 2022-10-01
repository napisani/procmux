from typing import List

from prompt_toolkit.application import get_app
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, VSplit
from prompt_toolkit.widgets import Button, TextArea

from app.context import ProcMuxContext
from app.interpolation import Interpolation
from app.log import logger
from app.tui.keybindings import register_app_wide_configured_keybindings, register_configured_keybinding
from app.tui.style import height_100, width_100


class CommandForm:
    def __init__(self, proc_idx: int):
        self._ctx = ProcMuxContext()
        interpolations = self.get_interpolations_for_process_id(proc_idx)
        self._tab_idx = 0

        start_button = Button(text='Start')
        cancel_button = Button(text='Cancel')
        self._text_inputs = [
            TextArea(
                height=1,
                prompt=f"{interp.field} >>> ",
                style="class:input-field",
                multiline=False,
                wrap_lines=False,
                text=interp.value,
                focus_on_click=True,
            ) for interp in interpolations
        ]
        self._focusable_components = [
            *self._text_inputs,
            start_button,
            cancel_button
        ]
        self._container = HSplit([
            *self._text_inputs,
            VSplit([
                start_button,
                cancel_button
            ])
        ],
            width=width_100,
            height=height_100,
            key_bindings=self._get_keybindings()
        )

    def _get_keybindings(self):
        kb = KeyBindings()

        def next_input(_event):
            logger.info('next_input - focusing on next tab index')
            self._tab_idx = (self._tab_idx + 1) % len(self._focusable_components)
            current_input = self._focusable_components[self._tab_idx]
            app = get_app()
            app.layout.focus(current_input)

        kb = register_configured_keybinding('next_input', next_input, kb)
        # kb = register_app_wide_configured_keybindings(kb)
        return kb

    def __pt_container__(self):
        return self._container

    @staticmethod
    def get_interpolations_for_process_id(proc_idx: int) -> List[Interpolation]:
        ctx = ProcMuxContext()
        proc_name = ctx.tui_state.process_name_list[proc_idx]
        proc = ctx.config.procs[proc_name]
        interpolations = proc.interpolations
        return interpolations
