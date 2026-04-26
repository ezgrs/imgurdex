import random
import typing

import fastapi
import httpx
import google.cloud.storage
import google.api_core.exceptions

from imgurbc.domain.interfaces.consumer import Consumer
from imgurbc.domain.interfaces.id_iterator import IdIterator
from imgurbc.infrastructure.services.consumer.upload_to_gcloud import (
    UploadToGoogleCloudStorageConsumer,
)
from imgurbc.infrastructure.services.downloader.httpx_impl import (
    HttpxDownloader,
)
from imgurbc.infrastructure.services.id_iterator.random_impl import (
    RandomIdIterator,
)

GCLOUD_STORAGE_BUCKET_NAME: typing.Final[str] = "imgurbc"
GCLOUD_STORAGE_BUCKET_LOCATION: typing.Final[str] = "us-east1"


def _create_id_iterator() -> IdIterator:
    return RandomIdIterator(rng=random.Random())


def _create_consumer() -> Consumer:
    client = google.cloud.storage.Client()
    bucket: google.cloud.storage.Bucket
    try:
        bucket = client.create_bucket(
            GCLOUD_STORAGE_BUCKET_NAME,
            location=GCLOUD_STORAGE_BUCKET_LOCATION,
        )
    except google.api_core.exceptions.Conflict:
        bucket = client.get_bucket(GCLOUD_STORAGE_BUCKET_NAME)
    return UploadToGoogleCloudStorageConsumer(bucket=bucket)


def create_app() -> fastapi.FastAPI:
    app = fastapi.FastAPI()

    @app.post("/imgur")
    async def _(
        id_iterator: typing.Annotated[
            IdIterator, fastapi.Depends(_create_id_iterator)
        ],
        consumer: typing.Annotated[Consumer, fastapi.Depends(_create_consumer)],
        imgur_id: typing.Annotated[str | None, fastapi.Body(embed=True)] = None,
    ):
        if imgur_id is None:
            imgur_id = next(id_iterator)

        async with httpx.AsyncClient() as client:
            downloader = HttpxDownloader(
                client=client,
                base_url=httpx.URL(scheme="https", host="i.imgur.com"),
            )
            resource = await downloader.download(imgur_id)
            if resource is None:
                await consumer.consume_miss(imgur_id)
            else:
                await consumer.consume_hit(resource)

    return app
