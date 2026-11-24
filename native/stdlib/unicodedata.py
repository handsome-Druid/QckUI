import unicodedata

from ._parse import parse

__all__: list[str] = parse(unicodedata)  # pyright: ignore[reportUnsupportedDunderAll]  # noqa: PLE0605
