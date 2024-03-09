import logging
from abc import ABC
from io import BytesIO
from pathlib import Path, PurePath
from typing import Sequence, BinaryIO, Mapping

import imageio as iio
import numpy as np
from aiofm.protocols.s3 import S3Protocol

logger = logging.getLogger(__name__)


class ImageFileStorage(ABC):
    IMAGE_FILE_EXTENSION = ''
    DATASET_SUBDIR_NAME = f'{IMAGE_FILE_EXTENSION}_files'
    METADATA_FILE_NAME = 'metadata.json'
    SUPPORTED_BPS: tuple[int] = ()

    def __init__(self, color_spaces: Mapping):
        self.color_spaces = color_spaces
        self.s3_protocol = None

    def __str__(self):
        return self.DATASET_SUBDIR_NAME

    def get_s3_client(self) -> S3Protocol:
        if not self.s3_protocol:
            self.s3_protocol = S3Protocol()

        return self.s3_protocol

    def _get_full_dst_file_path(self, target_dir_path: PurePath, file_name: str, bits: int, color_space: str):
        dst_dir_path = Path(target_dir_path, f'.{self.IMAGE_FILE_EXTENSION}{str(bits)}{color_space}')
        # dst_dir_path.mkdir(exist_ok=True)

        return Path(dst_dir_path, f'{file_name}.{self.IMAGE_FILE_EXTENSION}')

    def _save_image(self, uri: str | Path | BytesIO | BinaryIO, image: np.ndarray):
        iio.imwrite(uri, image, format=self.IMAGE_FILE_EXTENSION)

    def save_image(self, target_dir_path: PurePath, file_name: str, bits: int, color_space: str, image: np.ndarray):
        dst_path = self._get_full_dst_file_path(target_dir_path, file_name, bits, color_space)

        if str(target_dir_path).startswith('s3://'):
            with self.get_s3_client().open(dst_path, 'wb') as f:
                self._save_image(f, image)
        else:
            dst_path.parent.mkdir(exist_ok=True)

            with open(dst_path, 'wb') as f:
                self._save_image(f, image)

        logger.info(f'Saved converted image in: {str(dst_path)}')
