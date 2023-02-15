import concurrent.futures
import logging
import multiprocessing
from pathlib import Path
from typing import Generator, Sequence

import numpy as np
import rawpy
from python3_commons.fs import iter_files
from rawpy._rawpy import Params, RawPy

from dataset_image_converter.storages import ImageFileStorage

logger = logging.getLogger(__name__)


def _convert_raw(raw_image: RawPy, storages: Sequence[ImageFileStorage]):
    for storage in storages:
        for color_space in storage.color_spaces:
            for bits in storage.SUPPORTED_BPS:
                params = Params(
                    # demosaic_algorithm=DemosaicAlgorithm.DCB, dcb_iterations=1, dcb_enhance=True,
                    median_filter_passes=0, use_camera_wb=True, output_color=color_space, output_bps=bits,
                    no_auto_bright=True
                )
                processed_image = np.asarray(raw_image.postprocess(params))
                storage_dir_name = storage.IMAGE_FILE_EXTENSION
                color_space_name = str(color_space).split('.')[-1]

                logger.info(f'Converting {str(raw_image_path)} to {storage_dir_name}')

                storage.save_image(raw_image_path.parent, raw_image_path.name, bits, color_space_name,
                                   processed_image)


def convert_raw_from_s3(raw_image_path: str):
    # TODO: boto3, s3
    pass


def convert_raw_from_fs(raw_image_path: Path, storages: Sequence[ImageFileStorage]):
    raw_image = rawpy.imread(str(raw_image_path))

    _convert_raw(raw_image, storages)


def iter_fs_images(root: Path) -> Generator[Path, None, None]:
    return (
        file_path
        for file_path in iter_files(root)
        if file_path.name.lower().endswith('.arw')
    )


def convert_raws(root: Path, storages: Sequence[ImageFileStorage]) -> Sequence[str]:
    filenames = []

    with concurrent.futures.ProcessPoolExecutor(max_workers=multiprocessing.cpu_count() * 2) as executor:
        for image_path in iter_fs_images(root):
            executor.submit(convert_raw_from_fs, image_path, storages)
            filenames.append(image_path.name)

    return filenames
