import textwrap

from ._parse import parse

__all__: list[str] = parse(textwrap)  # pyright: ignore[reportUnsupportedDunderAll]  # noqa: PLE0605
