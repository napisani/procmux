import argparse

parser = argparse.ArgumentParser(description="procmux-tui")
parser.add_argument('--config',
                    required=True)
parser.add_argument('--config-override',
                    required=False)
cli_args = parser.parse_args()


