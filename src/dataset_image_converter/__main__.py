import argparse
import logging

from rawpy._rawpy import ColorSpace

from dataset_image_converter.convert import convert_raws
from dataset_image_converter.storages.containers import NumpyZipImageStorage
from dataset_image_converter.storages.fs import (
    JPEGImageStorage, PNGImageStorage, BMPImageStorage, TIFFImageStorage
)

logger = logging.getLogger(__name__)


def get_parsed_args():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--data-root', type=str)

    args, args_other = parser.parse_known_args()

    return args


def main():
    args = get_parsed_args()
    data_root_path = args.data_root

    color_spaces = {
        'raw': ColorSpace.raw,
        'srgb': ColorSpace.sRGB,
        # 'adobe': ColorSpace.Adobe,
        # 'aces': ColorSpace.ACES,
        'p3d65': ColorSpace.P3D65,
        'prophoto': ColorSpace.ProPhoto,
        'xyz': ColorSpace.XYZ,
        # 'wide': ColorSpace.Wide
    }
    storages = {
        'jpeg': (
            JPEGImageStorage(quality=100, color_spaces=color_spaces),
            # JPEGImageStorage(quality=75, color_spaces=color_spaces),
            # JPEGImageStorage(quality=50, color_spaces=color_spaces),
            # JPEGImageStorage(quality=25, color_spaces=color_spaces),
            # JPEGImageStorage(quality=10, color_spaces=color_spaces),
        ),
        # 'png': (PNGImageStorage(color_spaces=color_spaces), ),
        # 'bmp': (BMPImageStorage(color_spaces=color_spaces), ),
        'tiff': (TIFFImageStorage(color_spaces=color_spaces), ),
        # 'webp': (WebPImageStorage(), ),
        'numpy_zip': (NumpyZipImageStorage(color_spaces=color_spaces), ),
        # 'numpy_mmap': (NumpyMmapImageStorage(), ),
        # 'cupy': (CupyMmapImageStorage(), ),
    }

    convert_raws(data_root_path, storages)


main()
