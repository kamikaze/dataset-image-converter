import concurrent.futures
import logging
import multiprocessing
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
    for storage in storages:
        for color_space in storage.color_spaces:
            for bits in storage.SUPPORTED_BPS:
                params = Params(
                    # demosaic_algorithm=DemosaicAlgorithm.DCB, dcb_iterations=1, dcb_enhance=True,
                    median_filter_passes=0, use_camera_wb=True, output_color=color_space, output_bps=bits,
                    no_auto_bright=True
                )
                processed_image = raw_image.postprocess(params)
                processed_image = np.asarray(processed_image)
                storage_dir_name = storage.IMAGE_FILE_EXTENSION
                color_space_name = str(color_space).split('.')[-1]

                logger.info(f'Converting {raw_image_path} to {storage_dir_name}')

                storage.save_image(raw_image_path.parent, raw_image_path.name, bits, color_space_name,
                                   processed_image)


def convert_raw_from_s3(raw_image_path: PurePath, storages: Sequence[ImageFileStorage]):
    protocol = S3Protocol()

    with protocol.open(raw_image_path, 'rb') as f:
        raw_image = rawpy.imread(f.stream)

    _convert_raw(raw_image, PurePath(raw_image_path), storages)


def convert_raw_from_fs(raw_image_path: Path, storages: Sequence[ImageFileStorage]):
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
    filenames = []

    with concurrent.futures.ProcessPoolExecutor(max_workers=multiprocessing.cpu_count() * 2) as executor:
        root = PurePath(root.split('s3://', maxsplit=1)[1])

        for image_path in iter_s3_images(root):
            convert_raw_from_s3(image_path, storages)
            executor.submit(convert_raw_from_s3, image_path, storages)
            filenames.append(image_path.name)

    return filenames
