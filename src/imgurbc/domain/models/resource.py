import dataclasses
import typing

_MAGIC_NUMBERS: typing.Final[typing.Mapping[bytes, str]] = {
    b"\xff\xd8\xff\xe0": "jpg",
    b"\xff\xd8\xff\xe1": "jpg",
    b"\xff\xd8\xff\xe2": "jpg",
    b"\xff\xd8\xff\xe8": "jpg",
    b"\xff\xd8\xff\xee": "jpg",
    b"\xff\xd8\xff\xfe": "jpg",
    b"\xff\xd8\xff\xdb": "jpg",
    b"\x47\x49\x46\x38": "gif",
    b"\x89\x50\x4e\x47": "png",
}


@dataclasses.dataclass(kw_only=True, frozen=True)
class Resource:
    id: str
    """
    The ID of this resource in the Imgur website.

    It's composed by 7 characters that satisfy the regular expression 
    `[A-Za-z0-9]`.
    """

    raw_extension: str
    """
    The extension of this resource considered in the Imgur website.
    """

    contents: bytes = dataclasses.field(repr=False)
    """
    The contents of this resource.
    """

    @property
    def extension(self) -> str:
        """
        The extension of this resource.

        This field contains a non-dotted extension (e.g. "jpg", "png", "gif") that
        describe this resource contents, calculated by its first four bytes.
        """
        return _MAGIC_NUMBERS[self.contents[:4]]

    @property
    def raw_name(self) -> str:
        """
        The Imgur file name of this resource.

        The file name is composed of `id` followed by a dot followed by a extension.

        Its extension may nnot reflect the resource contents. This field will probably
        contain a *.png* extension, even if the resource is a JPG file, for example.
        Users should rely on [name] to a more precise value.
        """
        return f"{self.id}.{self.raw_extension}"

    @property
    def name(self) -> str:
        """
        The correct file name for this resource.

        The file name is composed of `id` followed by a dot followed by a extension.

        Since [raw_name] does not offer a precise file extension, this property
        replaces the imprecise extension with a more precise one:

        ```python
        resource = Resource(
            id="d5hU9pb",
            raw_extension="png",
            contents=b"\xff\xd8\xff\xe1...",
        )
        print(resource.raw_name)  # d5hU9pb.png
        print(resource.name)      # d5hU9pb.jpeg
        ```
        """
        return f"{self.id}.{self.extension}"
