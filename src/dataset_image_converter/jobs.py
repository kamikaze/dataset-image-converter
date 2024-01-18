import argparse
import asyncio
import logging.config
import os

from dataset_image_converter import object_storage
from dataset_image_converter.conf import LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)

logger = logging.getLogger(__name__)


async def update_storage_class():
    bucket = os.environ.get('S3_BUCKET', 'rtu-datasets')
    prefix = os.environ.get('S3_PREFIX', 'own_transport/')

    await object_storage.update_storage_class(bucket, prefix)


def get_parsed_args():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--job', type=str)

    args, args_other = parser.parse_known_args()

    return args


async def main():
    args = get_parsed_args()
    job_mapping = {
        'update_storage_class': update_storage_class,
    }

    try:
        job = job_mapping[args.job]
    except KeyError:
        logger.error(f'Unknown job: {args.job}')
    else:
        await job()

    logger.info(f'Job {args.job} finished')


if __name__ == '__main__':
    asyncio.run(main())
