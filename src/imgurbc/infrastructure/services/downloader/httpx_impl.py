import httpx
import http.client

from imgurbc.domain.interfaces.downloader import Downloader
from imgurbc.domain.models.resource import Resource


class HttpxDownloader(Downloader):
    _client: httpx.AsyncClient
    _base_url: httpx.URL

    def __init__(
        self, *, client: httpx.AsyncClient, base_url: httpx.URL
    ) -> None:
        self._client = client
        self._base_url = base_url

    @property
    def _referer_url(self) -> httpx.URL:
        host = self._base_url.host
        match host.split(".", 1):
            case [str()]:  # No dots on host
                return self._base_url
            case [str(), str() as domain] if "." in domain:  # Has a subdomain
                return self._base_url.copy_with(host=domain)
            case [str(), str()]:  # Doesn't have a submain
                return self._base_url
            case _:
                assert False, f"not a valid host: {host}"

    async def download(self, id: str) -> Resource | None:
        raw_extension = "png"

        response = await self._client.get(
            self._base_url.join(f"{id}.{raw_extension}"),
            headers={
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "accept-encoding": "gzip, deflate, br, zstd",
                "accept-language": "pt-BR,pt;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
                "cache-control": "no-cache",
                "pragma": "no-cache",
                "priority": "u=0, i",
                "referer": str(self._referer_url),
                "upgrade-insecure-requests": "1",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0",
                "sec-ch-ua": '"Microsoft Edge";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "same-site",
                "sec-fetch-user": "?1",
            },
        )
        if response.status_code == http.client.FOUND:
            location = response.headers["Location"]
            assert location == self._base_url.join(
                "removed.png"
            ), f"unexpected redirect location: {location}"
            return None

        response.raise_for_status()
        return Resource(
            id=id,
            raw_extension=raw_extension,
            contents=await response.aread(),
        )
