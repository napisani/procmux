import logging

from app.config import parse_config, ProcMuxConfig
from app.context import ProcMuxContext
from app.log import formatter, logger


def run_app(cfg: ProcMuxConfig):
    if cfg.log_file:
        file_handler = logging.FileHandler(cfg.log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    ProcMuxContext().bootstrap(cfg)
    from app.tui import start_tui
    start_tui()


if __name__ == '__main__':
    from args import cli_args, close_open_arg_resources

    config = parse_config(cli_args.config)
    close_open_arg_resources()
    run_app(config)
