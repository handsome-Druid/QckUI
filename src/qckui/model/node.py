from dataclasses import dataclass
from inspect import Parameter
from types import ModuleType
from typing import Literal, Protocol, override

from PySide6.QtCore import QObject


@dataclass(slots=True, frozen=True)
class Node:
    """Metadata describing a node class.

    Attributes:
        category: Directory name under which the node class is registered.
        module: Module containing the node class.
        cls: QObject subclass exported through the module's __all__.
        inputs: Parameters extracted from the __call__ signature.
        outputs: Class-level annotations of the form Annotated[Signal, type],
            mapping signal names to their emitted value types.
    """

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

    category: Literal["plugins", "nodes"]
    module: ModuleType
    cls: type[_NodeObject]
    inputs: dict[str, Parameter]
    outputs: dict[str, type]
