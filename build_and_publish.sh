#!/bin/bash
# clean
rm -rf ./dist/*
# package for distribution
python setup.py sdist bdist_wheel

# upload to pypi
twine upload --repository pypi --skip-existing dist/*
