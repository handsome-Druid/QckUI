import heapq

from ._parse import parse

__all__: list[str] = parse(heapq)  # pyright: ignore[reportUnsupportedDunderAll]  # noqa: PLE0605
