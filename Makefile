.PHONY: install run build test publish nixbuild nixdevelop nixrun

install:
	uv sync # isntall all requirements 

run:
	uv run procmux 

build:
	uv build

nixbuild: 
	nix build

nixdevelop: 
	nix develop .

nixrun: 
	nix run

test:
	uv run python -m pytest 

publish:
	uv publish
