import statistics

from ._parse import parse

__all__: list[str] = parse(statistics)  # pyright: ignore[reportUnsupportedDunderAll]  # noqa: PLE0605
