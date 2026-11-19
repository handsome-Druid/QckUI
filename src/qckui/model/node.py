from dataclasses import dataclass
from inspect import Parameter
from typing import Protocol, override

from PySide6.QtCore import QObject


@dataclass(slots=True, frozen=True)
class Node:
    class _NodeObject(Protocol):
        class _Inputs:
            type Args = object
            type Kwargs = object

        def __call__(self, *args: _Inputs.Args, **kwargs: _Inputs.Kwargs) -> object:
            """Return value ignored; typically returns None"""

        @override
        def __init__(
            self, /, parent: QObject | None = None, *, objectName: str | None = None
        ): ...

    path: str
    cls: type[_NodeObject]
    inputs: dict[str, Parameter]
    outputs: dict[str, type]
