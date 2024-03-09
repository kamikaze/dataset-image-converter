import concurrent.futures
import logging
from functools import partial
from pathlib import Path, PurePath
from typing import Generator, Sequence, Mapping

import colour.io
import numpy as np
import rawpy
from aiofm.protocols.s3 import S3Protocol
from exif import Image
from python3_commons.fs import iter_files
from rawpy._rawpy import Params, RawPy
from tifffile import TiffFile

from dataset_image_converter.storages import ImageFileStorage

logger = logging.getLogger(__name__)


def _save_image(image: np.ndarray, raw_image_path: PurePath, storage: ImageFileStorage, color_space, bits: int):
    storage_dir_name = storage.IMAGE_FILE_EXTENSION
    color_space_name = str(color_space).split('.')[-1]

    logger.info(f'Converting {raw_image_path} to {storage_dir_name}')

    storage.save_image(raw_image_path.parent, raw_image_path.name, bits, color_space_name, image)


def _convert_raw(raw_image: RawPy, raw_image_path: PurePath, storages: Mapping[str, Sequence[ImageFileStorage]]):
    """
    Converting input raw image to different storage formats.
    Extracting all color spaces, so we can process RAW once per color space to save CPU time.
    """

    camera_profile_path = Path(Path(__file__).parent, 'SONY_ILCE-7RM4_iso100_FE_70_200mm_F2.8_GM_OSS_f5.6_daylight.dcp')

    with open(camera_profile_path, 'rb') as f:
        camera_profile = f.read()

    color_spaces = {
        color_space_name: color_space
        for storage_set in storages.values()
        for storage in storage_set
        for color_space_name, color_space in storage.color_spaces.items()
    }

    for color_space_name, color_space in color_spaces.items():
        params = Params(
            # demosaic_algorithm=DemosaicAlgorithm.DCB, dcb_iterations=1, dcb_enhance=True,
            median_filter_passes=0, use_camera_wb=True, output_color=color_space, output_bps=16,
            no_auto_bright=True
        )
        processed_image = raw_image.postprocess(params)
        processed_image = np.asarray(processed_image)

        for storage_set in storages.values():
            for storage in storage_set:
                if 16 in storage.SUPPORTED_BPS and color_space_name in storage.color_spaces:
                    _save_image(processed_image, raw_image_path, storage, color_space_name, 16)

        processed_image_8bit = (processed_image // 256).astype(np.uint8)
        del processed_image

        for storage_set in storages.values():
            for storage in storage_set:
                if 8 in storage.SUPPORTED_BPS and color_space_name in storage.color_spaces:
                    _save_image(processed_image_8bit, raw_image_path, storage, color_space_name, 8)

        del processed_image_8bit


def convert_raw_from_s3(storages: Mapping[str, Sequence[ImageFileStorage]], raw_image_path: PurePath) -> PurePath:
    protocol = S3Protocol()

    with protocol.open(raw_image_path, 'rb') as f:
        raw_image = rawpy.imread(f.stream)

    _convert_raw(raw_image, PurePath(raw_image_path), storages)

    del raw_image

    return raw_image_path


def convert_raw_from_fs(storages: Mapping[str, Sequence[ImageFileStorage]], raw_image_path: Path):
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


def convert_raws(root: str, storages: Mapping[str, Sequence[ImageFileStorage]]) -> Sequence[str]:
    if root.startswith('s3://'):
        root = PurePath(root.split('s3://', maxsplit=1)[1])
        convert_raw_partial = partial(convert_raw_from_s3, storages)
        file_iterator = iter_s3_images(root)
    else:
        root = Path(root)
        convert_raw_partial = partial(convert_raw_from_fs, storages)
        file_iterator = iter_files(root)

    with concurrent.futures.ProcessPoolExecutor(max_workers=32) as executor:
        futures = executor.map(convert_raw_partial, file_iterator)
        filenames = list(futures)

    return filenames
