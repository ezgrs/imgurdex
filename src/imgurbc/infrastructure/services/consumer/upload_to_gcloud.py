import asyncio
import mimetypes

from imgurbc.domain.interfaces.consumer import Consumer
from imgurbc.domain.models.resource import Resource

import google.cloud.storage


class UploadToGoogleCloudStorageConsumer(Consumer):
    _bucket: google.cloud.storage.Bucket

    def __init__(self, *, bucket: google.cloud.storage.Bucket) -> None:
        self._bucket = bucket

    async def consume_miss(self, id: str) -> None:
        return

    async def consume_hit(self, resource: Resource) -> None:
        blob = self._bucket.blob(resource.name)
        content_type, _ = mimetypes.guess_type(resource.name)
        assert content_type, f"unexpected extension: {resource.name}"
        await asyncio.to_thread(
            blob.upload_from_string,
            resource.contents,
            content_type=content_type,
        )
