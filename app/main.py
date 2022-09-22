from app.config import parse_config
from app.context import ProcMuxContext
from args import cli_args, close_open_arg_resources


def run():
    config = parse_config(cli_args.config)
    ProcMuxContext().bootstrap(config)
    close_open_arg_resources()
    from app.tui import start_tui
    start_tui()


if __name__ == '__main__':
    run()
