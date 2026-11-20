from typing import Annotated, Protocol, runtime_checkable

from PySide6.QtCore import QObject, Signal

from . import truediv

__all__: list[str] = ["Mul", "truediv"]


class Mul(QObject):
    result: Annotated[Signal, object] = Signal(object)

    @runtime_checkable
    class Mulable(Protocol):
        def __mul__(self, other: object) -> object: ...

    def __call__(self, x: Mulable, y: object) -> None:
        self.result.emit(x * y)
