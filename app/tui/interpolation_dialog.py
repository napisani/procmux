from typing import Callable, List, Optional
from prompt_toolkit.application import get_app
from prompt_toolkit.layout import Dimension, Float, FloatContainer, HSplit, VSplit
from prompt_toolkit.widgets import Box, Button, Frame, TextArea

from app.config import ProcMuxConfig
from app.log import logger
from app.tui.keybindings import DocumentedKeybindings
from app.tui.types import Process
from app.util.interpolation import Interpolation


class InterpolationDialog():
    def __init__(self,
                 process: Process,
                 run_in_background: bool,
                 config: ProcMuxConfig,
                 float_container: FloatContainer,
                 on_finished: Callable[[Process, bool, Optional[List[Interpolation]]], None]
                 ):
        self._process = process
        self._run_in_background = run_in_background
        self._interpolations = process.config.interpolations
        self._config = config
        self._float_container = float_container
        self._on_finished = on_finished
        self._tab_ix = 0

        self._text_inputs = [
            TextArea(
                height=1,
                width=50,
                prompt=self._config.layout.field_replacement_prompt.replace('__FIELD_NAME__', interp.field),
                style="class:input-field",
                multiline=False,
                wrap_lines=False,
                text=interp.default_value,
                focus_on_click=True,
            ) for interp in self._interpolations
        ]
        self._move_cursors_to_last_character()

        start_button = Button('Start', self._on_start)
        cancel_button = Button('Cancel', self._on_cancel)
        self._focusable_components = [*self._text_inputs, start_button, cancel_button]

        self._container = HSplit(
            [
                Box(
                    body=HSplit(
                        children=self._text_inputs,
                        padding=1
                    ),
                    padding=Dimension(min=1, max=1, preferred=1),
                    padding_bottom=0
                ),
                Box(
                    body=VSplit(
                        children=[start_button, cancel_button],
                        padding=Dimension(min=1, max=5, preferred=5)
                    ),
                    height=Dimension(min=1, max=3, preferred=3)
                )
            ]
        )

    def _move_cursors_to_last_character(self):
        for ti in self._text_inputs:
            buff = ti.control.buffer
            buff.cursor_position = len(buff.document.current_line_after_cursor)

    def _on_start(self):
        final_input_interpolations: List[Interpolation] = []
        for input_field, interp in zip(self._text_inputs, self._interpolations):
            final_input_interpolations.append(Interpolation(
                field=interp.field,
                value=input_field.text,
                default_value=interp.default_value
            ))
        self._float_container.floats = []
        self._on_finished(self._process, self._run_in_background, final_input_interpolations)

    def _on_cancel(self):
        self._float_container.floats = []
        self._on_finished(self._process, self._run_in_background, None)

    def _move_focus(self, direction: int):
        self._tab_ix = (self._tab_ix + direction) % len(self._focusable_components)
        current_input = self._focusable_components[self._tab_ix]
        app = get_app()
        if app:
            app.layout.focus(current_input)

    def get_keybindings(self) -> DocumentedKeybindings:
        def next_input():
            logger.info('interpolation dialog next_input - focusing on next tab index')
            self._move_focus(1)

        def previous_input():
            logger.info('interpolation dialog previous_input - focusing on next tab index')
            self._move_focus(-1)

        kb = DocumentedKeybindings()
        kb.register_configured_keybinding_sans_event(self._config.keybinding.next_input, next_input, 'next input')
        kb.register_configured_keybinding_sans_event(
            self._config.keybinding.previous_input, previous_input, 'previous input')
        kb.register_configured_keybinding_sans_event(self._config.keybinding.submit_dialog, self._on_start, 'start')
        kb.register_configured_keybinding_sans_event(self._config.keybinding.cancel_dialog, self._on_cancel, 'cancel')
        return kb

    def start_interpolation(self):
        app = get_app()
        if app and self._text_inputs:
            self._float_container.floats = [Float(Frame(self._container, self._process.name))]
            app.layout.focus(self._text_inputs[0])
        else:
            self._on_cancel()
