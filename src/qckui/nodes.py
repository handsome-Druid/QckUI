from collections.abc import Iterable, Iterator, Mapping
from enum import StrEnum
from importlib.machinery import ModuleSpec, all_suffixes
from importlib.metadata import EntryPoints, entry_points
from importlib.util import module_from_spec, spec_from_file_location
from inspect import (
    Parameter,
    getattr_static,
    getmodulename,
    isclass,
    isfunction,
    ismodule,
    signature,
)
from logging import Logger, getLogger
from sys import modules, platform
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

from PySide6.QtCore import QDir, QFileInfo, QObject, QStandardPaths, Signal, Slot

from qckui.model import Node, QABCMeta

_logger: Logger = getLogger(name=__name__)


class Nodes(Mapping[str, Node], QObject, metaclass=QABCMeta):
    _nodes: ClassVar[dict[str, Node]] = {}
    changed = Signal()

    class Category(StrEnum):
        Native = "native"
        Plugins = "plugins"
        Extensions = "extensions"

    def __init__(
        self, /, parent: QObject | None = None, *, objectName: str | None = None
    ) -> None:
        super().__init__(parent, objectName=objectName)
        if platform == "android" or "__compiled__" in globals():
            root_dir = QDir(
                path=QStandardPaths.writableLocation(
                    QStandardPaths.StandardLocation.AppDataLocation
                )
            )
        else:
            root_dir: QDir = QFileInfo(__file__).dir()
            for _ in range(2):
                if not root_dir.cdUp():
                    raise OSError(
                        self.tr("Failed to find the root directory of the package.")
                    )
        self._dir: dict[str, QDir] = {
            Nodes.Category.Native: QDir(path=root_dir.absoluteFilePath("native")),
            Nodes.Category.Plugins: QDir(path=root_dir.absoluteFilePath("plugins")),
        }

    def _load(self, name: str, category: str, /) -> None:
        info = QFileInfo(self._dir[category].absoluteFilePath(name))
        if info.isFile():
            spec: ModuleSpec | None = spec_from_file_location(
                name=category
                + "."
                + (getmodulename(path=info.fileName()) or info.fileName()),
                location=info.absoluteFilePath(),
            )
        elif info.isDir():
            spec = spec_from_file_location(
                name=category + "." + info.fileName(),
                location=info.absoluteFilePath() + "/__init__.py",
                submodule_search_locations=[info.absoluteFilePath()],
            )
        elif info.exists():
            raise RuntimeError(
                self.tr("Path is not a file or directory: {path}").format(
                    path=info.absoluteFilePath()
                )
            )
        elif (
            info_ := next(
                (
                    info_
                    for suffix in all_suffixes()
                    if (info_ := QFileInfo(info.absoluteFilePath() + suffix)).exists()
                ),
                None,
            )
        ) is not None:
            spec = spec_from_file_location(
                name=category + "." + info.fileName(),
                location=info_.absoluteFilePath(),
            )
        else:
            entry_info_list: list[QFileInfo] = info.dir().entryInfoList(
                (info.fileName() + ".*",),
                filters=QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot,
            )
            if entry_info_list:
                for info_ in entry_info_list:
                    try:
                        self._load(info_.fileName(), category)
                    except Exception:
                        _logger.exception(
                            self.tr("Failed to load: {}").format(
                                info.absoluteFilePath()
                            )
                        )
                    continue
            elif "." in info.fileName():
                origin: QFileInfo = info
                while not info.exists():
                    if "." not in info.fileName():
                        raise RuntimeError(
                            self.tr("Path is not a file or directory: {path}").format(
                                path=origin.absoluteFilePath()
                            )
                        )
                    info = QFileInfo(
                        info.absoluteFilePath().rsplit(sep=".", maxsplit=1)[0]
                    )
                    if not info.exists():
                        for suffix in all_suffixes():
                            info_ = QFileInfo(info.absoluteFilePath() + suffix)
                            if info_.exists():
                                info: QFileInfo = info_
                                break
                file_name: str = info.fileName()
                self._load(
                    file_name,
                    category,
                )
            else:
                raise RuntimeError(
                    self.tr("Path is not a file or directory: {path}").format(
                        path=info.absoluteFilePath()
                    )
                )
            return
        if spec is None:
            raise RuntimeError(
                self.tr("Could not create a module spec for: {path}").format(
                    path=info.absoluteFilePath()
                )
            )
        if spec.loader is None:
            raise RuntimeError(
                self.tr("No module loader is available for: {path}").format(
                    path=info.absoluteFilePath()
                )
            )
        module: ModuleType = module_from_spec(spec)
        key: str = spec.name
        modules[key] = module
        spec.loader.exec_module(module)
        self._load_module(module)

    def _load_module(self, module: ModuleType, /) -> None:
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
            path: str = module.__name__ + "." + name
            try:
                self._load_node(path, getattr(module, name, None))
            except Exception:
                _logger.exception(msg=self.tr("Failed to load {}").format(path))
                continue

    def _load_node(self, path: str, cls: object, /) -> None:
        if not isclass(object=cls) or not issubclass(cls, QObject):
            if ismodule(object=cls):
                self._load_module(cls)
            else:
                _logger.warning(msg=self.tr("{} is not a QObject.").format(path))
            return
        if getattr_static(obj=cls, attr="__call__", default=None) is getattr_static(
            obj=type(cls), attr="__call__", default=None
        ) or not callable(cls.__call__):
            _logger.warning(msg=self.tr("{} is not a callable object.").format(path))
            return
        inputs: dict[str, Parameter] = {}
        for i, (n, param) in enumerate(
            iterable=signature(obj=cls.__call__).parameters.items()
        ):
            if i == 0 and isfunction(object=getattr_static(obj=cls, attr="__call__")):
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

    @Slot(str)
    def reload(self, path: str | Category, /) -> None:
        category, _, module_name = path.partition(".")
        if category != self.Category.Extensions:
            nodes_bak: dict[str, Node] = {
                key: self._nodes.pop(key)
                for key in tuple(self._nodes)
                if key == path or key.startswith(path + ".")
            }
        else:
            if not module_name:
                nodes_bak = {
                    key: self._nodes.pop(key)
                    for key in tuple(self._nodes)
                    if not key.startswith(
                        (self.Category.Native + ".", self.Category.Plugins + ".")
                    )
                }
            else:
                nodes_bak = {
                    key: self._nodes.pop(key)
                    for key in tuple(self._nodes)
                    if key == module_name or key.startswith(module_name + ".")
                }
        try:
            if not module_name:
                if category == self.Category.Extensions:
                    eps: EntryPoints = entry_points(group="qckui.extensions")
                    for key in tuple(modules):
                        if any(
                            key == ep.module or key.startswith(ep.module + ".")
                            for ep in eps
                        ):
                            del modules[key]
                    for ep in eps:
                        try:
                            if ep.attr:
                                self._load_node(
                                    ep.module + "." + ep.name,
                                    ep.load(),
                                )
                            else:
                                self._load_module(ep.load())
                        except Exception:
                            _logger.exception(
                                msg=self.tr("Failed to load extension: {}").format(
                                    ep.value
                                )
                            )
                            continue
                else:
                    for key in tuple(modules):
                        if key.startswith(category + "."):
                            del modules[key]
                    for info in self._dir[category].entryInfoList(
                        filters=QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot,
                    ):
                        if info.fileName() == "__pycache__":
                            continue
                        try:
                            self._load(info.fileName(), category)
                        except Exception:
                            _logger.exception(
                                msg=self.tr("Failed to load: {}").format(
                                    info.absoluteFilePath()
                                )
                            )
                            continue
            else:
                if category == self.Category.Extensions:
                    for key in tuple(modules):
                        if key == module_name or key.startswith(module_name + "."):
                            del modules[key]
                    for ep in entry_points(group="qckui.extensions"):
                        if ep.module == module_name or ep.module.startswith(
                            module_name + "."
                        ):
                            try:
                                if ep.attr:
                                    self._load_node(
                                        ep.module + "." + ep.name,
                                        ep.load(),
                                    )
                                else:
                                    self._load_module(ep.load())
                            except Exception:
                                _logger.exception(
                                    msg=self.tr("Failed to load extension: {}").format(
                                        ep.value
                                    )
                                )
                                continue
                else:
                    for key in tuple(modules):
                        if key == path or key.startswith(path + "."):
                            del modules[key]
                    self._load(module_name, category)
        except BaseException:
            self._nodes.update(nodes_bak)
            raise
        self.changed.emit()

    @override
    def __iter__(self) -> Iterator[str]:
        yield from self._nodes

    @override
    def __len__(self) -> int:
        return len(self._nodes)

    @override
    def __getitem__(self, key: str) -> Node:
        return self._nodes[key]
