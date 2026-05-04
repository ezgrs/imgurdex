import os
import random
import typing
import http.client

import dotenv
import fastapi
import httpx
import google.cloud.storage
import google.api_core.exceptions

from imgurbc.domain.interfaces.consumer import Consumer
from imgurbc.domain.interfaces.id_iterator import IdIterator
from imgurbc.infrastructure.services.consumer.combiner import CombinerConsumer
from imgurbc.infrastructure.services.consumer.send_email import (
    SendEmailConsumer,
)
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


def _create_google_cloud_storage_consumer() -> Consumer:
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


def _create_email_consumer() -> Consumer:
    return SendEmailConsumer(
        host=os.environ["EMAIL_HOST"],
        port=int(os.environ["EMAIL_PORT"]),
        username=os.environ["EMAIL_USERNAME"],
        password=os.environ["EMAIL_PASSWORD"],
    )


def _create_consumer() -> Consumer:
    return CombinerConsumer(
        consumers=[
            # _create_google_cloud_storage_consumer(),
            _create_email_consumer(),
        ]
    )


def create_app() -> fastapi.FastAPI:
    dotenv.load_dotenv()

    app = fastapi.FastAPI()

    id_iterator = _create_id_iterator()
    consumer = _create_consumer()

    async def _fetch_image(imgur_id: str) -> fastapi.Response:
        async with httpx.AsyncClient() as client:
            downloader = HttpxDownloader(
                client=client,
                base_url=httpx.URL(scheme="https", host="i.imgur.com"),
            )
            resource = await downloader.download(imgur_id)
            if resource is None:
                await consumer.consume_miss(imgur_id)
                return fastapi.Response(status_code=http.client.NOT_FOUND)

            await consumer.consume_hit(resource)
            return fastapi.Response(status_code=http.client.OK)

    @app.post("/imgur/random")
    async def fetch_random_imgur_image() -> fastapi.Response:
        return await _fetch_image(next(id_iterator))

    @app.post("/imgur/{imgur_id}")
    async def fetch_imgur_image(
        imgur_id: typing.Annotated[str, fastapi.Path()],
    ) -> fastapi.Response:
        return await _fetch_image(imgur_id)

    return app
