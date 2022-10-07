from typing import Dict, List, Optional

from app.config import ProcMuxConfig, ProcessConfig
from app.tui.types import Process


class ProcessState:
    def __init__(self, config: ProcMuxConfig):
        self.config: ProcMuxConfig = config
        self.process_list: List[Process] = self._create_process_list(self.config.procs)
        self.filtered_process_list: List[Process] = self.process_list
        self.selected_process: Optional[Process] = self.filtered_process_list[0] if self.filtered_process_list else None
        self._filter: str = ''

    @property
    def is_selected_process_running(self) -> bool:
        return self.selected_process.running if self.selected_process else False

    @property
    def has_running_processes(self) -> bool:
        for process in self.process_list:
            if process.running:
                return True
        return False

    @property
    def filter_text(self) -> str:
        return self._filter

    def select_first_process(self):
        if self.filtered_process_list:
            self.selected_process = self.filtered_process_list[0]

    def set_selected_process_by_y_pos(self, y_pos: int):
        if self.filtered_process_list and y_pos >= 0 and y_pos < len(self.filtered_process_list):
            self.selected_process = self.filtered_process_list[y_pos]

    def _create_process_list(self, process_config: Dict[str, ProcessConfig]) -> List[Process]:
        return self._sort_process_list(
            [Process(ix, pc, n) for ix, (n, pc) in enumerate(process_config.items())])

    def _sort_process_list(self, ps: List[Process]) -> List[Process]:
        if self.config.layout.sort_process_list_alpha:
            return sorted(ps, key=lambda p: p.name)
        return ps

    def apply_filter(self, filter_text: str):
        self._filter = filter_text

        if not self._filter:
            self.filtered_process_list = self._sort_process_list(self.process_list)

        prefix = self.config.layout.category_search_prefix

        def filter_against_category(search_text: str, process: Process) -> bool:
            search_t = search_text[len(prefix):]
            if not process.config.categories:
                return False
            categories = {c.lower() for c in process.config.categories}
            return search_t.lower() in categories

        def filter_against_name_and_meta(search_text: str, process: Process) -> bool:
            tags = set()
            if process.config.meta_tags:
                for tag in process.config.meta_tags:
                    tags.add(tag.lower())
            return search_text.lower() in process.name or search_text.lower() in tags

        def filter_(search_text: str, process: Process) -> bool:
            if search_text.startswith(prefix):
                return filter_against_category(search_text, process)
            return filter_against_name_and_meta(search_text, process)

        self.filtered_process_list = self._sort_process_list([p for p in self.process_list if filter_(self._filter, p)])
        self.selected_process = self.filtered_process_list[0] if self.filtered_process_list else None
