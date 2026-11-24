import json

from ._parse import parse

__all__: list[str] = parse(json)  # pyright: ignore[reportUnsupportedDunderAll]  # noqa: PLE0605
