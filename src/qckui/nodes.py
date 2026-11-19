from collections.abc import Iterable, Iterator, MutableMapping
from inspect import (
    Parameter,
    getattr_static,
    isclass,
    isfunction,
    ismodule,
    signature,
)
from logging import Logger, getLogger
from types import ModuleType
from typing import (
    Annotated,
    ClassVar,
    Literal,
    get_args,
    get_origin,
    get_type_hints,
    override,
)

from PySide6.QtCore import QObject, Signal

from qckui.model import Node, QABCMeta

_logger: Logger = getLogger(name=__name__)


class Nodes(MutableMapping[str, Node], QObject, metaclass=QABCMeta):
    _nodes: ClassVar[dict[str, Node]] = {}

    def _load_module(self, prefix: str, module: ModuleType, /) -> None:
        __all__: list[object] | None = getattr(module, "__all__", None)
        if not isinstance(__all__, Iterable):
            _logger.warning(
                msg=self.tr(
                    "Module '{name}' does not define an __all__ attribute."
                ).format(name=module.__name__)
            )
            return
        for name in __all__:
            if not isinstance(name, str):
                _logger.warning(
                    msg=self.tr(
                        "Module '{module}' defines a non-string name in __all__: {name}"
                    ).format(module=module.__name__, name=name)
                )
                continue
            path: str = ".".join((prefix.strip("."), module.__name__, name))
            try:
                cls: object = getattr(module, name, None)
                if not isclass(object=cls) or not issubclass(cls, QObject):
                    if ismodule(object=cls):
                        self._load_module(prefix, cls)
                    else:
                        _logger.warning(
                            msg=self.tr(
                                "Module '{module}' defines a non-QObject class in __all__: {name}"
                            ).format(module=name, name=name)
                        )
                    continue
                if not callable(getattr(cls, "__call__", None)):  # noqa: B004
                    _logger.warning(
                        msg=self.tr(
                            "Module '{module}' defines a non-callable object in __all__: {name}"
                        ).format(module=name, name=name)
                    )
                    continue
                inputs: dict[str, Parameter] = {}
                for i, (n, param) in enumerate(
                    iterable=signature(obj=cls.__call__).parameters.items()
                ):
                    if i == 0 and isfunction(
                        object=getattr_static(obj=cls, attr="__call__")
                    ):
                        continue
                    if get_origin(param.annotation) is not Literal:
                        try:
                            issubclass(type, param.annotation)
                        except TypeError:
                            _logger.exception(
                                msg=self.tr(
                                    "Parameter '{name}' cannot have a parameterized generic annotation."
                                ).format(name=n)
                            )
                            break
                    inputs[n] = param
                else:
                    outputs: dict[str, type] = {}
                    for n, tp in get_type_hints(obj=cls, include_extras=True).items():
                        if n.startswith("_") or get_origin(tp) is not Annotated:
                            continue
                        args: tuple[object, ...] = get_args(tp)
                        if (
                            len(args) < 2
                            or args[0] is not Signal
                            or not isinstance(args[1], type)
                        ):
                            _logger.warning(
                                msg=self.tr(
                                    "The type annotation for '{name}' must specify a type."
                                ).format(name=n)
                            )
                            continue
                        outputs[n] = args[1]
                    self._nodes[path] = Node(
                        path,
                        cls,  # pyright: ignore[reportArgumentType]
                        inputs,
                        outputs,
                    )
            except Exception:
                _logger.exception(msg=self.tr("Failed to load {}").format(path))
                continue

    @override
    def __iter__(self) -> Iterator[str]:
        yield from self._nodes

    @override
    def __len__(self) -> int:
        return len(self._nodes)

    @override
    def __getitem__(self, key: str) -> Node:
        return self._nodes[key]
