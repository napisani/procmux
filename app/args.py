import argparse

parser = argparse.ArgumentParser(description="procmux-tui")
parser.add_argument('--config',
                    type=argparse.FileType('r', encoding='UTF-8'),
                    required=True)
cli_args = parser.parse_args()


def close_open_arg_resources():
    cli_args.config.close()
