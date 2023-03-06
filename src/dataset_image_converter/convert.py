import concurrent.futures
import logging
import multiprocessing
from functools import partial
from pathlib import Path, PurePath
from typing import Generator, Sequence

import numpy as np
import rawpy
from aiofm.protocols.s3 import S3Protocol
from python3_commons.fs import iter_files
from rawpy._rawpy import Params, RawPy

from dataset_image_converter.storages import ImageFileStorage

logger = logging.getLogger(__name__)


def _convert_raw(raw_image: RawPy, raw_image_path: PurePath, storages: Sequence[ImageFileStorage]):
    """
    Converting input raw image to different storage formats.
    Extracting all color spaces, so we can process RAW once per color space to save CPU time.
    """
    color_spaces = {color_space for storage in storages for color_space in storage.color_spaces}

    for color_space in color_spaces:
        params = Params(
            # demosaic_algorithm=DemosaicAlgorithm.DCB, dcb_iterations=1, dcb_enhance=True,
            median_filter_passes=0, use_camera_wb=True, output_color=color_space, output_bps=16,
            no_auto_bright=True
        )
        processed_image = raw_image.postprocess(params)
        processed_image = np.asarray(processed_image)

        for storage in storages:
            if color_space in storage.color_spaces:
                for bits in storage.SUPPORTED_BPS:
                    storage_dir_name = storage.IMAGE_FILE_EXTENSION
                    color_space_name = str(color_space).split('.')[-1]

                    logger.info(f'Converting {raw_image_path} to {storage_dir_name}')

                    storage.save_image(raw_image_path.parent, raw_image_path.name, bits, color_space_name,
                                       processed_image)


def convert_raw_from_s3(storages: Sequence[ImageFileStorage], raw_image_path: PurePath) -> PurePath:
    protocol = S3Protocol()

    with protocol.open(raw_image_path, 'rb') as f:
        raw_image = rawpy.imread(f.stream)

    _convert_raw(raw_image, PurePath(raw_image_path), storages)

    return raw_image_path


def convert_raw_from_fs(storages: Sequence[ImageFileStorage], raw_image_path: Path):
    raw_image = rawpy.imread(str(raw_image_path))

    _convert_raw(raw_image, raw_image_path, storages)


def iter_fs_images(root: Path) -> Generator[Path, None, None]:
    return (
        file_path
        for file_path in iter_files(root)
        if file_path.name.lower().endswith('.arw')
    )


def iter_s3_images(root: PurePath) -> Generator[PurePath, None, None]:
    protocol = S3Protocol()

    return (
        file_path
        for file_path in protocol.ls(root)
        if file_path.name.lower().endswith('.arw')
    )


def convert_raws(root: str, storages: Sequence[ImageFileStorage]) -> Sequence[str]:
    root = PurePath(root.split('s3://', maxsplit=1)[1])
    convert_raw_from_s3_partial = partial(convert_raw_from_s3, storages)

    with concurrent.futures.ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()-1) as executor:
        futures = executor.map(convert_raw_from_s3_partial, iter_s3_images(root))
        filenames = list(futures)

    return filenames
