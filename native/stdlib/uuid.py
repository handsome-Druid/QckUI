import uuid

from ._parse import parse

__all__: list[str] = parse(uuid)  # pyright: ignore[reportUnsupportedDunderAll]  # noqa: PLE0605
