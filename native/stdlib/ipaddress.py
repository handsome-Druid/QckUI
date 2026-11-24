import ipaddress

from ._parse import parse

__all__: list[str] = parse(ipaddress)  # pyright: ignore[reportUnsupportedDunderAll]  # noqa: PLE0605
