import zlib

from ._parse import parse

__all__: list[str] = parse(zlib)  # pyright: ignore[reportUnsupportedDunderAll]  # noqa: PLE0605
