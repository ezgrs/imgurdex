import mimetypes
import email.message

import aiosmtplib

from imgurbc.domain.interfaces.consumer import Consumer
from imgurbc.domain.models.resource import Resource


class SendEmailConsumer(Consumer):
    host: str
    port: int
    username: str
    password: str

    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str,
        password: str,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    async def consume_miss(self, id: str) -> None:
        return

    async def consume_hit(self, resource: Resource) -> None:
        message = email.message.EmailMessage()
        message["From"] = self.username
        message["To"] = self.username
        message["Subject"] = f"📸 You've got a new image! ({resource.id})"
        message.set_content(
            (
                "Hi there,\n\n"
                "I just found a new image for you 🎉\n\n"
                "I've attached it to this email so you can take a look.\n\n"
                "Have a great day!\n"
            )
        )

        mime_type, _ = mimetypes.guess_type(resource.name)
        if mime_type is None:
            mime_type = "application/octet-stream"

        main_type, sub_type = mime_type.split("/", 1)

        message.add_attachment(
            resource.contents,
            maintype=main_type,
            subtype=sub_type,
            filename=resource.name,
        )
        await aiosmtplib.send(
            message,
            hostname=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            start_tls=True,
        )
