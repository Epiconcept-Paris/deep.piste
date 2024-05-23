# deep.piste

Tools for implementing Deep.piste study.

## Installation

### Prerequisites

**On windows:**

You may need to install ["Visual C++ Redistributable Packages for Visual Studio 2013" Microsoft C++ Build Tools](https://www.microsoft.com/en-us/download/details.aspx?id=40784).

**On Ubuntu:**
```bash
sudo apt-get install python3-tk
```

### Installation

```bash
pip install deep-piste
```

### Installation for contributors

1. Download source code

```bash
git clone https://github.com/Epiconcept-Paris/kskit.git
git clone https://github.com/Epiconcept-Paris/deep.piste.git
```

2. Create and activate a virtual environment

```bash
cd deep.piste/
python3 -m venv env
. env/bin/activate
```

3. Install [kskit](https://github.com/Epiconcept-Paris/kskit)

```bash
cd ../kskit
pip install -e .
```

4. Install deep.piste

```bash
cd ../deep.piste
pip install -e .
```

### Checking installation

1. Checking kskit installation

Open a python interpreter and try to deidentify a dicom file:
```python
from kskit.dicom.deid_mammogram import deidentify_image_png

deidentify_image_png(
    "/path/to/mammogram.dcm",
    "/path/to/processed/output-folder",
    "output-filename"
)
```

2. Checking deep.piste installation

When writing the following command, you should be able to see the help menu:
```bash
>>> python3 -m dpiste -h

usage: __main__.py [-h] {extract,transform,export,backup} ...

positional arguments:
  {extract,transform,export,backup}
	extract         	Invoke initial extractions commands
	transform       	Perform transformation on input data
	export          	Sending data
	backup          	Back up data

options:
  -h, --help        	show this help message and exit
```

## Tools for developers

## Installation

```bash
pip install -e .[quality-tools]
```

## Usage

Format your files with `python3 -m autopep8 --in-place file/to/format`

Lint your files with `python3 -m pylint file/to/lint`
