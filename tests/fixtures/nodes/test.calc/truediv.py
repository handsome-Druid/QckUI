from typing import Annotated, Protocol, runtime_checkable

from PySide6.QtCore import QObject, Signal

__all__: list[str] = ["Truediv"]


class Truediv(QObject):
    result: Annotated[Signal, object] = Signal(object)

    @runtime_checkable
    class Truedivable(Protocol):
        def __truediv__(self, other: object) -> object: ...

    def __call__(self, x: Truedivable, y: object) -> None:
        self.result.emit(x / y)
