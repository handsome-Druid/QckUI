import html

from ._parse import parse

__all__: list[str] = parse(html)  # pyright: ignore[reportUnsupportedDunderAll]  # noqa: PLE0605
