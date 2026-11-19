from collections.abc import Iterable
from graphlib import TopologicalSorter
from itertools import chain, combinations
from types import NoneType
from typing import Protocol, runtime_checkable

from PySide6.QtGui import QImage


@runtime_checkable
class ImagesType(Protocol):
    def images(self) -> Iterable[QImage]: ...


def _sorted(types: Iterable[type], /) -> list[type]:
    graph: dict[type, set[type]] = {}
    for x, y in combinations(iterable=types, r=2):
        graph.setdefault(x, set())
        graph.setdefault(y, set())
        try:
            if issubclass(x, y):
                graph[y].add(x)
            elif issubclass(y, x):
                graph[x].add(y)
        except TypeError:
            pass
    return list(TopologicalSorter(graph).static_order())


literals: list[type] = _sorted((int, float, bool, str, NoneType))
types: list[type] = _sorted(chain(literals, (QImage, ImagesType)))
