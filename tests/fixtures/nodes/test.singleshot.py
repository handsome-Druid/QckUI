from typing import Annotated

from PySide6.QtCore import QObject, QTimer, Signal

__all__: list[str] = ["SingleShot"]


class SingleShot(QObject):
    output: Annotated[Signal, object] = Signal(object)

    def __call__(self, input: object, msec: int = 0) -> None:
        QTimer.singleShot(msec, lambda: self.output.emit(input))
