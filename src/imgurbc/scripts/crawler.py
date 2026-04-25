import argparse
import asyncio
import random
import sys
import typing

import aiopath
import httpx
import pydantic

from imgurbc.domain.interfaces.consumer import Consumer
from imgurbc.domain.interfaces.id_iterator import IdIterator
from imgurbc.infrastructure.services.consumer.combiner import CombinerConsumer
from imgurbc.infrastructure.services.consumer.output_to_stream import (
    OutputToStreamConsumer,
)
from imgurbc.infrastructure.services.consumer.store_as_local_file import (
    StoreAsLocalFileConsumer,
)
from imgurbc.infrastructure.services.consumer.upload_to_gcloud import (
    UploadToGoogleCloudStorageConsumer,
)
from imgurbc.infrastructure.services.downloader.httpx_impl import (
    HttpxDownloader,
)
from imgurbc.infrastructure.services.id_iterator.combiner import (
    CombinerIdIterator,
)
from imgurbc.infrastructure.services.id_iterator.memory import MemoryIdIterator
from imgurbc.infrastructure.services.id_iterator.random_impl import (
    RandomIdIterator,
)


class Args(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    delay: int
    inputs: typing.Annotated[
        list[str], pydantic.Field([], validation_alias="input")
    ]
    output_dir_path: typing.Annotated[
        aiopath.AsyncPath | None,
        pydantic.Field(None, validation_alias="output"),
    ]
    no_stdout: typing.Annotated[
        bool, pydantic.Field(False, validation_alias="no-stdout")
    ]
    gcloud_storage_bucket_name: typing.Annotated[
        str | None,
        pydantic.Field(None, validation_alias="gcloud_storage_bucket_name"),
    ]
    gcloud_storage_bucket_location: typing.Annotated[
        str,
        pydantic.Field(None, validation_alias="gcloud_storage_bucket_location"),
    ]


def parse_args() -> typing.Mapping[str, typing.Any]:
    parser = argparse.ArgumentParser(
        prog="crawler",
        description="A crawler that collects random images from Imgur",
    )
    parser.add_argument(
        "-d",
        "--delay",
        type=int,
        default=1,
        help="Delay between tries, in seconds",
    )
    parser.add_argument(
        "--gcloud-storage-bucket-name",
        type=str,
        required=False,
        help="Name of the Google Cloud Storage bucket",
    )
    parser.add_argument(
        "--gcloud-storage-bucket-location",
        type=str,
        default="us-east1",
        help=(
            "Location of the Google Cloud Storage bucket. It's only used if "
            "the provided bucket name does not exist."
        ),
    )
    parser.add_argument(
        "-i", "--input", nargs="+", default=[], help="Input as strings"
    )
    parser.add_argument(
        "--no-stdout",
        action="store_true",
        help="Do not print to standard output",
    )
    parser.add_argument(
        "-o", "--output", type=aiopath.AsyncPath, help="Output directory"
    )
    return parser.parse_args().__dict__


async def main() -> None:
    args = Args(**parse_args())

    # Create root IdIterator to generate IDs
    id_iterators: list[IdIterator] = []
    if args.inputs:
        id_iterators.append(MemoryIdIterator(iterator=iter(args.inputs)))
    if not id_iterators:
        id_iterators.append(RandomIdIterator(rng=random.Random()))
    id_iterator = CombinerIdIterator(iterators=iter(id_iterators))

    # Create root Consumer to execute actions
    consumers: list[Consumer] = []
    if args.output_dir_path is not None:
        consumers.append(
            StoreAsLocalFileConsumer(base_dir=args.output_dir_path)
        )
    if not args.no_stdout:
        consumers.append(OutputToStreamConsumer(stream=sys.stdout))

    gcloud_storage_bucket_name = args.gcloud_storage_bucket_name
    if gcloud_storage_bucket_name is not None:
        import google.cloud.storage
        import google.api_core.exceptions

        client = google.cloud.storage.Client()
        bucket: google.cloud.storage.Bucket
        try:
            bucket = client.create_bucket(
                gcloud_storage_bucket_name,
                location=args.gcloud_storage_bucket_location,
            )
        except google.api_core.exceptions.Conflict:
            bucket = client.get_bucket(gcloud_storage_bucket_name)
        consumers.append(UploadToGoogleCloudStorageConsumer(bucket=bucket))

    consumer = CombinerConsumer(consumers=consumers)

    async with httpx.AsyncClient() as client:
        downloader = HttpxDownloader(
            client=client,
            base_url=httpx.URL(scheme="https", host="i.imgur.com"),
        )
        for id in id_iterator:
            resource = await downloader.download(id)
            await asyncio.sleep(args.delay)
            if resource is None:
                await consumer.consume_miss(id)
            else:
                await consumer.consume_hit(resource)


if __name__ == "__main__":
    asyncio.run(main())
