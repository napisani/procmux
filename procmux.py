from app.__main__ import run_app
from app.config import parse_config
from app.args import cli_args


def start_cli():
    config = parse_config(cli_args.config, cli_args.config_override)
    run_app(config)


if __name__ == '__main__':
    start_cli()
