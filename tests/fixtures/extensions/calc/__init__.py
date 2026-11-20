from typing import Annotated, Protocol, overload, runtime_checkable

from PySide6.QtCore import QObject, Signal

__all__: list[str] = ["Sub"]


class Add(QObject):
    @runtime_checkable
    class Addable(Protocol):
        def __add__(self, other: object) -> object: ...

    result: Annotated[Signal, object] = Signal(object)

    def __call__(self, x: Addable, y: object) -> None:
        self.result.emit(x + y)


class Sub(QObject):
    @runtime_checkable
    class Subbable(Protocol):
        def __sub__(self, other: object) -> object: ...

    @runtime_checkable
    class Rsubbable(Protocol):
        def __rsub__(self, other: object) -> object: ...

    result: Annotated[Signal, object] = Signal(object)

    @overload
    def __call__(self, x: Subbable, y: object) -> None: ...
    @overload
    def __call__(self, x: object, y: Rsubbable) -> None: ...
    def __call__(self, x: object, y: object) -> None:
        if not isinstance(x, self.Subbable) and not isinstance(y, self.Rsubbable):
            raise TypeError
        self.result.emit(x - y)  # pyright: ignore[reportOperatorIssue]
