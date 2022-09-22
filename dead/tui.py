from asyncio import sleep
from dataclasses import fields
import io
import threading

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.app import App
from textual.geometry import Size
from textual.reactive import Reactive
from textual.widget import Widget
from textual.widgets import Placeholder, ScrollView

from app.config import KeybindingConfig
from app.context import ProcMuxContext


class ProcessNameWidget(Widget):

    def __init__(self, *, name=None, is_selected=False) -> None:
        super().__init__(name=name)
        self._style_config = ProcMuxContext().config.style
        self.is_selected = is_selected

    def render(self) -> str:
        if self.is_selected:
            return f"[bold {self._style_config.selected_process_color} on {self._style_config.selected_process_bg_color}]{self.name}[/]"
        return f"[{self._style_config.unselected_process_color}]{self.name}[/]"


class Terminal(Widget):
    def __init__(self, name=None) -> None:
        super().__init__(name=name)
        self._output = []
        self.ctx = ProcMuxContext()

    def on_mount(self):
        self.set_interval(2, self._refresh_output)

    def _refresh_output(self):
        if not self.ctx.tui_state.selected_process_name:
            self._output = []
        else:
            manager = self.ctx.proc_managers[self.ctx.tui_state.selected_process_name]
            if manager._proc and manager._proc.stdout and not manager._proc.stdout.closed:
                stdout = manager._proc.stdout
                with io.TextIOWrapper(stdout, encoding="utf-8") as lines:
                    for line in lines:
                        self._output.append(line)
        self.refresh()

    def render(self) -> Panel:

        max_line_size = 40
        if len(self._output) != 0:
            max_line_size = max([len(line) for line in self._output])

        size = Size(width=max_line_size, height=len(self._output))
        return Align(
            '\n'.join(self._output))
        # return Panel(
        #     '\n'.join(self._output),
        #     title="Processes",
        #     height=20
        #     # title=f"[{self.colors['color_title']}]{self.title} ({len(self.post_list)})",
        #     # border_style=self.border_style,
        # )


class SideBar(Widget):

    def __init__(self, name=None) -> None:
        super().__init__(name=name)

    def render(self) -> Panel:
        ctx = ProcMuxContext()
        grid = Table.grid(expand=True)
        for name in ctx.tui_state.process_name_list:
            manager = ctx.proc_managers[name]
            process_name_widget = ProcessNameWidget(name=name)
            process_name_widget.is_selected = ctx.tui_state.selected_process_name == name
            grid.add_row(
                process_name_widget,
                (f"[{ctx.config.style.status_running_color}]RUNNING[/]"
                 if manager.is_running() else
                 f"[{ctx.config.style.status_stopped_color}]STOPPED[/]")
            )
        return Panel(
            grid,
            title="Processes",
            # title=f"[{self.colors['color_title']}]{self.title} ({len(self.post_list)})",
            # border_style=self.border_style,
        )


#
# class SideBar(GridView):
#     async def on_mount(self) -> None:
#         # define input fields
#         # self.grid.set_align("center", "center")
#         self.grid.set_gap(1, 1)
#         # Create rows / columns / areas
#         self.grid.add_column("Processes")
#         self.grid.add_column("Status")
#         service = ProcessesService()
#         # self.grid.add_row("row", repeat=len(service.proc_managers), size=1)
#
#         for name, manager in service.proc_managers.items():
#             name_content = Text(overflow="ellipsis", no_wrap=True)
#             name_content.append(name)
#             status_content = Text(overflow="ellipsis", no_wrap=True)
#             status_content.append("RUNNING" if manager.is_running() else "STOPPED")
#             self.grid.add_row(name=name)
#             # self.grid.add_widget(name)
#             # self.grid.add_widget(name)
#
#         # # Place out widgets in to the layout
#         # button_style = "bold red on white"
#         # label_style = "bold white on rgb(60,60,60)"
#         # username_label = Button(label="username", name="username_label", style=label_style)
#         # password_label = Button(label="password", name="password_label", style=label_style)
#         # self.grid.add_widget(username_label)
#         # self.grid.add_widget(Placeholder())
#         # self.grid.add_widget(password_label)
#         # self.grid.add_widget(Placeholder())
#         # self.grid.add_widget(Button(label="register", name="register", style=button_style))
#         # self.grid.add_widget(Button(label="login", name="login", style=button_style))


class ProcMuxTUI(App):
    async def on_load(self, event):
        keybinding_config = ProcMuxContext().config.keybinding
        for keybinding_field in fields(KeybindingConfig):
            keybinding = getattr(keybinding_config, keybinding_field.name)
            if type(keybinding) == str:
                keybinding = [keybinding]
            for key in keybinding:
                await self.bind(key, keybinding_field.name)

    def _prep_tui_state(self):
        ctx = ProcMuxContext()
        ctx.tui_state.process_name_list = sorted(ctx.proc_managers.keys())
        ctx.tui_state.selected_process_name = None
        if ctx.proc_managers:
            [first, *_] = ctx.tui_state.process_name_list
            ctx.tui_state.selected_process_name = first

    async def on_mount(self) -> None:
        self._prep_tui_state()
        # self.terminal = Panel(, title="exec")
        self.side_bar = SideBar()
        self.terminal = Terminal()
        side_bar_scroll_wrapper = ScrollView(contents=self.side_bar, gutter=1)
        terminal_wrapper = ScrollView(contents=self.terminal, gutter=1)
        await self.view.dock(side_bar_scroll_wrapper, edge="left", size=30)
        await self.view.dock(self.terminal, edge="top")

    async def _action_move_proc_selection(self, offset: int):
        tui_state = ProcMuxContext().tui_state
        index = tui_state.process_name_list.index(tui_state.selected_process_name)
        index += offset
        if -1 < index < len(tui_state.process_name_list):
            tui_state.selected_process_name = tui_state.process_name_list[index]
            self.side_bar.refresh()

    async def action_up(self):
        await self._action_move_proc_selection(-1)

    async def action_down(self):
        await self._action_move_proc_selection(1)

    async def action_start(self):
        ctx = ProcMuxContext()
        tui_state = ctx.tui_state
        if tui_state.selected_process_name:
            manager = ctx.proc_managers[tui_state.selected_process_name]
            if not manager.is_running() and self.terminal:
                manager.start()
                self.side_bar.refresh()
                self.terminal.refresh()
                # manager.start()
                # self.terminal.update(output)
                # self.terminal.refresh()

    async def action_stop(self):
        ctx = ProcMuxContext()
        tui_state = ctx.tui_state
        if tui_state.selected_process_name:
            manager = ctx.proc_managers[tui_state.selected_process_name]
            if manager.is_running():
                manager.send_stop_signal()
