import colorsys

from ._parse import parse

__all__: list[str] = parse(colorsys)  # pyright: ignore[reportUnsupportedDunderAll]  # noqa: PLE0605
