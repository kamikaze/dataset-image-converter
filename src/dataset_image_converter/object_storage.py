import asyncio
from asyncio import Semaphore

from aiobotocore.session import get_session
from types_aiobotocore_s3 import S3Client
from types_aiobotocore_s3.literals import StorageClassType

MAX_CONCURRENT_REQUESTS = 20


async def update_storage_class_for_key(client: S3Client, bucket: str, key: str, semaphore: Semaphore,
                                       storage_class: StorageClassType = 'STANDARD'):
    async with semaphore:
        copy_source = {'Bucket': bucket, 'Key': key}

        await client.copy_object(Bucket=bucket, Key=key, CopySource=copy_source, StorageClass=storage_class)


async def update_storage_class(bucket: str, prefix: str = None):
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    session = get_session()

    async with session.create_client('s3') as client:
        paginator = client.get_paginator('list_objects_v2')

        async for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            tasks = []

            for obj in page.get('Contents', []):
                tasks.append(update_storage_class_for_key(client, bucket, obj['Key'], semaphore))

            await asyncio.gather(*tasks)
