.PHONY: install run build test

install:
	uv sync # isntall all requirements 

run:
	uv run procmux 

build:
	uv build

nixbuild: 
	nix build
nixrun: 
	nix run

test:
	uv run python -m pytest -vv -s 


# install_library:
#     uv sync # pip install -r 
#     uv pip install -e . # replace pip install -e . requirements.in
# run_a_script:
#     uv run python ./my_lib/my_script.py # replace python ./my_lib/my_script.py
# launch_test:
#     uv run pytest -n auto --cov-report=xml # replace uv run pytest -n auto --cov-report=xml
