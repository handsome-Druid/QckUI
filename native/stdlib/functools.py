import functools

from ._parse import parse

__all__: list[str] = parse(functools)  # pyright: ignore[reportUnsupportedDunderAll]  # noqa: PLE0605
