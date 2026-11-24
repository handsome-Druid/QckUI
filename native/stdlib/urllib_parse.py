import urllib.parse

from ._parse import parse

__all__: list[str] = parse(urllib.parse)  # pyright: ignore[reportUnsupportedDunderAll]  # noqa: PLE0605
