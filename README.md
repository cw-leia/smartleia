[![Build Status](https://travis-ci.com/cw-leia/smartleia.svg?branch=master)](https://travis-ci.com/cw-leia/smartleia)

# SmartLeia

This repository holds the source of the python package used to drive the LEIA
smartcard reader. With it, you will be able to:

    - Connect to the LEIA board
    - Choose parameters for the PSS/PTS negotiation
    - Send APDUs and receive the corresponding responses
    - Activate the DFU mode to download new firmware
    - Start a [Virtual SmartCard](https://frankmorgner.github.io/vsmartcard/) 
      client to use LEIA as a real smartcard reader (through pcscd)

## Installation

### From pipy

```sh
python3 -m pip install smartleia
```

### From git


You may need to use the last version of python builtin's setuptools to install
smartleia from git

```sh
python3 -m pip install --upgrade pip setuptools wheel
```

```sh
git clone https://github.com/cw-leia/smartleia
cd smartleia
python3 -m pip install .
```

## Development setup
### Setup development environment


#### 1. Install python3-venv

```sh
sudo apt install python3-venv python3-pip
```

#### 2. Install poetry

```sh
python3 -m pip install poetry
```

#### 3. Install dependencies

It is time to install the dependencies and the dev dependencies of smartleia.
All what is needed to build doc, run tests, lint or format the python files will be installed **without polluting you system python installation**.


```sh
poetry install
```

#### 5. (Optionnal) Install git pre-commit hooks


```sh
poetry run pre-commit install
```
