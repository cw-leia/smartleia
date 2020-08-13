[![Build Status](https://travis-ci.com/cw-leia/smartleia.svg?branch=master)](https://travis-ci.com/cw-leia/smartleia)

# SmartLeia

This repository holds the source of the python package used to drive the LEIA
smart card reader. With it, you will be able to:

1. Connect to the LEIA board
2. Choose parameters for the PSS/PTS negotiation
3. Send APDUs and receive the corresponding responses
4. Activate the DFU mode to download new firmware
5. Start a [Virtual SmartCard](https://frankmorgner.github.io/vsmartcard/) 
client to use LEIA as a 'real' smart card reader (through PCSCD relay)

The documentation dedicated to the SmartLeia package can be found [here](https://github.com/cw-leia/smartleia-doc),
please check it to have details about the basic usage and the API for advanced
development features.

## Dependencies

You can install the requirements of the package using:

```sh
pip install requirements.txt
```

If you want to use the [Virtual SmartCard](https://frankmorgner.github.io/vsmartcard/) PCSCD
relay, you will need to install it either from packages (if your distro packages it) or
from sources by compiling it.

## Installation of smartleia

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
`````

### From pipy

```sh
python3 -m pip install smartleia
```
