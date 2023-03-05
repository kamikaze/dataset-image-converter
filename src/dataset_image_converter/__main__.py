import argparse
import logging
from typing import Sequence

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

    color_spaces = (
        ColorSpace.sRGB,
        ColorSpace.Adobe,
        ColorSpace.ACES,
        ColorSpace.ProPhoto,
        ColorSpace.XYZ,
        ColorSpace.Wide
    )
    storages: Sequence = (
        JPEGImageStorage(quality=100, color_spaces=color_spaces),
        JPEGImageStorage(quality=75, color_spaces=color_spaces),
        JPEGImageStorage(quality=50, color_spaces=color_spaces),
        JPEGImageStorage(quality=25, color_spaces=color_spaces),
        JPEGImageStorage(quality=10, color_spaces=color_spaces),
        PNGImageStorage(color_spaces=color_spaces),
        BMPImageStorage(color_spaces=color_spaces),
        TIFFImageStorage(color_spaces=color_spaces),
        # WebPImageStorage(),
        NumpyZipImageStorage(color_spaces=color_spaces),
        # NumpyMmapImageStorage(),
        # CupyMmapImageStorage(),
    )

    convert_raws(data_root_path, storages)


main()
