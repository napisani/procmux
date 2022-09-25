# test packaging

```bash
cd ~/code/procmux
#create a virtual env
pipx install virtualenv
virtualenv scratch_venv

#activate the new scratch venv
source scratch_venv/bin/activate

#package in development mode
python setup.py develop

# test that the new cli is available in the path
which procmux
#test app
procmux --config file.yaml
```

# testing publishing

```bash
# package for distribution
python setup.py sdist bdist_wheel

# upload to the TEST pypi repo
twine upload --repository testpypi --skip-existing dist/*
#enter user and password


cd /tmp/
virtualenv venv
cd venv/
activate bin/activate
# paste url from above twine command here
pip install -i https://test.pypi.org/simple/ procmux
procmux
```

# Publish for real

```bash

# package for distribution
python setup.py sdist bdist_wheel

# upload to the TEST pypi repo
twine upload --repository https://pypi.org --skip-existing dist/*
#enter user and password


cd /tmp/
virtualenv venv
cd venv/
activate bin/activate
# paste url from above twine command here
pip install -i https://pypi.org/procmux/ procmux
procmux

```