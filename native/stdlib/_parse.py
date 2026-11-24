from collections.abc import Callable
from functools import wraps
from inspect import Parameter, Signature, currentframe, isfunction, signature
from types import FrameType, ModuleType
from typing import (
    Annotated,
    Any,
    Concatenate,
    Self,
    override,
)

from PySide6.QtCore import QObject, QTimer, Signal


class _ExcStr(str):
    _exc: BaseException

    @override
    def __new__(cls, exc: BaseException, /) -> Self:
        self: Self = super().__new__(cls, object=exc)
        self._exc = exc
        return self

    def exception(self) -> BaseException:
        return self._exc


def parse(module: ModuleType, /) -> list[str]:
    __all__: list[str] = []
    for name in getattr(module, "__all__", None) or (
        name for name in dir(module) if not name.startswith("_")
    ):
        func: object = getattr(module, name)
        if not isfunction(func):
            continue
        try:
            sig: Signature = signature(obj=func)
        except TypeError, ValueError:
            continue
        if any(
            param.kind in (Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD)
            for param in sig.parameters.values()
        ):
            continue
        cls_name: str = "".join(
            part[:1].upper() + part[1:] for part in name.split(sep="_")
        )

        class StdObject(QObject):
            result: Annotated[
                Signal,
                sig.return_annotation
                if sig.return_annotation is not Signature.empty
                else Any,
            ] = Signal(object)
            exception: Annotated[Signal, _ExcStr] = Signal(object)

        def wrap[**P](
            func: Callable[P, Any] = func,
        ) -> Callable[Concatenate[StdObject, P], None]:
            @wraps(wrapped=func)
            def wrapped(self: StdObject, *args: P.args, **kwargs: P.kwargs) -> None:
                try:
                    result: object = func(*args, **kwargs)
                except BaseException as e:
                    exc = _ExcStr(e)
                    QTimer.singleShot(0, lambda: self.exception.emit(exc))
                    raise
                QTimer.singleShot(0, lambda: self.result.emit(result))

            return wrapped

        currentframe_: FrameType | None = currentframe()
        assert currentframe_ is not None
        f_back: FrameType | None = currentframe_.f_back
        assert f_back is not None
        f_back.f_globals[cls_name] = type(
            cls_name, (StdObject,), {"__call__": wrap(func)}
        )
        __all__.append(cls_name)
    return __all__
