import itertools

from ._parse import parse

__all__: list[str] = parse(itertools)  # pyright: ignore[reportUnsupportedDunderAll]  # noqa: PLE0605
