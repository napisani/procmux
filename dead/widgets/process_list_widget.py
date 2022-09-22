import itertools
import subprocess
from copy import deepcopy
from enum import Enum, auto
from pathlib import Path
from typing import Dict, Optional

from rich.panel import Panel
from rich.table import Table
from textual.widget import Widget

DEFAULT_EDITOR = "vi {file}"
DEFAULT_COLORS = {
    "color_focused_task": "red",
    "color_focused_task_priority": "bright_black",
    "color_focused_task_date": "bright_black",
    "color_default_task": "purple",
    "color_default_task_priority": "bright_black",
    "color_default_task_date": "bright_black",
    "color_focused_border": "#e8bde3",
    "color_default_border": "#c122ac",
    "color_title": "#e1af66",
}




def keys_on_file(post: frontmatter.Post) -> Dict[str, str]:
    return {
        key: value for key, value in frontmatter.load(post.get("path")).metadata.items()
    }


class Status(Enum):
    todo = auto()
    doing = auto()
    done = auto()

    def next(self):
        if self.value == len(self._member_names_):
            return Status(1)
        else:
            return Status(self.value + 1)

    def previous(self):
        if self.value == 1:
            return Status(len(self._member_names_))
        else:
            return Status(self.value - 1)


class Posts(Widget):
    def __init__(self, markata: "Markata", title: str, filter: str):
        super().__init__(title)
        self.m = markata
        self.config = self.m.get_plugin_config("todoui") or {}
        self.colors = self.config.get("colors", DEFAULT_COLORS)

        self.title = title
        self.name = title
        self.filter = filter
        self.is_selected = True
        self.current_post = DummyPost("")
        self.update()
        self.next_post()

    def update(self, reload: bool = False) -> None:
        current_uuid = self.current_post.get("uuid", None)
        if reload:
            self.m.glob()
            self.m.load()

        self.post_list = sorted(
            self.m.filter(self.filter), key=lambda x: x["priority"], reverse=True
        )
        self.post_cycle = itertools.cycle(self.post_list)
        if not self.post_list:
            self.current_post = DummyPost("")
        elif current_uuid is not None:
            self.select_post_by_id(current_uuid)
        self.refresh()

    def text(self) -> Optional[str]:
        return self.current_post.content

    def render(self) -> Panel:
        grid = Table.grid(expand=True)

        for post in self.post_list:
            if (
                    post.get("uuid", "") == self.current_post.get("uuid", "")
                    and self.is_selected
            ):
                grid.add_row(
                    f"[{self.colors['color_focused_task']}]{post.get('title')}",
                    f"[{self.colors['color_focused_task_priority']}]({post.get('priority')})[/]",
                    f"[{self.colors['color_focused_task_date']}]{post.get('date')}[/]",
                )
            else:
                grid.add_row(
                    f"[{self.colors['color_default_task']}]{post.get('title')}",
                    f"[{self.colors['color_default_task_priority']}]({post.get('priority')})[/]",
                    f"[{self.colors['color_default_task_date']}]{post.get('date')}[/]",
                )
        if self.is_selected:
            self.border_style = f"{self.colors['color_focused_border']}"
        else:
            self.border_style = f"{self.colors['color_default_border']}"
        return Panel(
            grid,
            title=f"[{self.colors['color_title']}]{self.title} ({len(self.post_list)})",
            border_style=self.border_style,
        )

    def previous_post(self) -> None:
        if len(self.post_list):
            for _ in range(len(self.post_list) - 1):
                self.current_post = next(self.post_cycle)
        self.refresh()

    def __next__(self) -> frontmatter.Post:
        return self.next_post()

    def next_post(self) -> frontmatter.Post:
        try:
            self.current_post = next(self.post_cycle)
        except StopIteration:
            ...
        self.refresh()

    def select_post_by_id(self, uuid: str) -> frontmatter.Post:
        while uuid != self.current_post.get("uuid", ""):
            self.current_post = next(self.post_cycle)

    def select_post_by_index(self, index) -> frontmatter.Post:
        uuid = self.post_list[index].get("uuid")
        while uuid != self.current_post["uuid"]:
            self.current_post = next(self.post_cycle)
        self.refresh()

    def move_next(self) -> None:
        if self.is_dummy:
            return
        post = deepcopy(self.current_post)
        path = Path(post["path"])
        post.metadata = keys_on_file(post)
        post["status"] = Status(Status._member_map_[post["status"]]).next().name
        path.write_text(frontmatter.dumps(post))
        self.update()

    def raise_priority(self) -> None:
        if self.is_dummy:
            return
        post = deepcopy(self.current_post)
        path = Path(post["path"])
        post.metadata = keys_on_file(post)
        post["priority"] = post["priority"] + 1
        path.write_text(frontmatter.dumps(post))
        self.update(reload=True)

    def lower_priority(self) -> None:
        if self.is_dummy:
            return
        post = deepcopy(self.current_post)
        path = Path(post["path"])
        post.metadata = keys_on_file(post)
        post["priority"] = post["priority"] - 1
        path.write_text(frontmatter.dumps(post))
        self.update(reload=True)

    def open_post(self) -> None:
        if self.is_dummy:
            return
        post = self.current_post
        editor = self.config.get("editor", DEFAULT_EDITOR)
        cmd = eval("f'" + editor + "'", {"file": post.get("path")})
        proc = subprocess.Popen(
            cmd,
            shell=True,
        )
        proc.wait()
        self.update(reload=True)

    def move_previous(self) -> None:
        if self.is_dummy:
            return
        post = deepcopy(self.current_post)
        path = Path(post["path"])
        post.metadata = keys_on_file(post)
        post["status"] = Status(Status._member_map_[post["status"]]).previous().name
        path.write_text(frontmatter.dumps(post))
        self.update()

    def delete_current(self) -> None:
        if self.is_dummy:
            return
        Path(self.current_post["path"]).unlink()
        self.update(reload=True)
        self.next_post()
        uuid = self.current_post.get("uuid")
        self.select_post_by_id(uuid)
