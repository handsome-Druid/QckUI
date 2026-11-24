import random

from ._parse import parse

__all__: list[str] = parse(random)  # pyright: ignore[reportUnsupportedDunderAll]  # noqa: PLE0605
