# Brigid CLI

`brigid-cli` has commands for interacting with Brigid's API, and other things.


## Installing brigid-cli

brigid-cli is a pure python package.  As such, it can be installed in the usual python ways.  For the following
instructions, either install it into your global python install, or use a python [virtual
environment](https://python-guide-pt-br.readthedocs.io/en/latest/dev/virtualenvs/) to install it without polluting your
global python environment.

### Install via pip

    pip install brigid-cli

### Install via `setup.py`

Download a release from [Github](https://github.com/caltechads/deployfish/releases), then:

    unzip brigid-cli-0.1.0.zip
    cd brigid-cli-0.1.0
    python setup.py install

Or:

    git clone https://github.com/caltechads/brigid-cli.git
    cd brigid-cli
    python setup.py install
