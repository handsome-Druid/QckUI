import operator

from ._parse import parse

__all__: list[str] = parse(operator)  # pyright: ignore[reportUnsupportedDunderAll]  # noqa: PLE0605
