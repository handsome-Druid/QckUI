import difflib

from ._parse import parse

__all__: list[str] = parse(difflib)  # pyright: ignore[reportUnsupportedDunderAll]  # noqa: PLE0605
