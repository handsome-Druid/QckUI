import string

from ._parse import parse

__all__: list[str] = parse(string)  # pyright: ignore[reportUnsupportedDunderAll]  # noqa: PLE0605
