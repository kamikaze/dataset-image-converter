# dataset-image-converter
This package converts RAW images into different image formats / containers.

## Installation

Make sure you have some system deps installed:
```bash
sudo apt install pkg-config libhdf5-dev
```

```bash
python3.11 -m venv venv --upgrade-deps
source venv/bin/activate
python -m pip install -U -r requirements_dev.txt

# For some reason h5py fails to install Cython while it needs it
python -m pip install -U Cython

python setup.py develop
```

## Running dataset format benchmark
```bash
python -m dataset_image_converter --data-root /path/to/datasets/
```
