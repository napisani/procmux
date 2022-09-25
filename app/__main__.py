import logging

from app.config import ProcMuxConfig
from app.context import ProcMuxContext
from app.log import formatter, logger


def run_app(cfg: ProcMuxConfig):
    if cfg.log_file:
        file_handler = logging.FileHandler(cfg.log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    ProcMuxContext().bootstrap(cfg)
    from app.tui.app import start_tui
    start_tui()


