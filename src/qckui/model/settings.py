from abc import ABCMeta
from collections.abc import Iterator, MutableMapping
from typing import NoReturn, Self, overload, override

from PySide6.QtCore import QObject, QSettings, Slot
from PySide6.QtGui import QUndoCommand, QUndoStack


class QABCMeta(ABCMeta, type(QObject)): ...


class Settings(QUndoStack, QSettings, MutableMapping[str, object], metaclass=QABCMeta):
    _NULL = object()

    class _SetValue(QUndoCommand):
        @override
        def __init__(
            self,
            settings: QSettings,
            key: str,
            value: object,
            /,
            parent: QUndoCommand | None = None,
        ) -> None:
            super().__init__(parent)
            self._settings: QSettings = settings
            self._key: str = key
            self._new_value: object = value
            self._old_value: object = settings.value(
                self._key, defaultValue=Settings._NULL
            )

        @override
        def redo(self) -> None:
            self._settings.setValue(self._key, self._new_value)

        @override
        def undo(self) -> None:
            if self._old_value is Settings._NULL:
                self._settings.remove(self._key)
            else:
                self._settings.setValue(self._key, self._old_value)

    class _Remove(QUndoCommand):
        @override
        def __init__(
            self, settings: QSettings, key: str, /, parent: QUndoCommand | None = None
        ) -> None:
            super().__init__(parent)
            self._settings: QSettings = settings
            self._key: str = key
            if not self._key:
                self._old_values: dict[str, object] = {
                    key: settings.value(key) for key in settings.allKeys()
                }
            else:
                self._old_value: object = settings.value(
                    key, defaultValue=Settings._NULL
                )

        @override
        def redo(self) -> None:
            self._settings.remove(self._key)

        @override
        def undo(self) -> None:
            if getattr(self, "_old_value", Settings._NULL) is not Settings._NULL:
                self._settings.setValue(self._key, self._old_value)
            elif hasattr(self, "_old_values"):
                for key, value in self._old_values.items():
                    self._settings.setValue(key, value)

    @override
    def __init__(
        self,
        fileName: str,
        format: QSettings.Format = QSettings.Format.IniFormat,
        /,
        parent: QObject | None = None,
        *,
        undoLimit: int = 32,
        group: str | None = None,
    ) -> None:
        super().__init__(parent, undoLimit=undoLimit)
        settings = super(QUndoStack, self)
        settings.__init__(fileName, format, parent)
        if group is not None:
            settings.beginGroup(group)

    @Slot(str, "QVariant")
    @override
    def setValue(self, key: str, value: object, /) -> None:
        super().push(self._SetValue(super(QUndoStack, self), key, value))

    @overload
    def value(self, key: str, /) -> object: ...

    @overload
    def value(
        self, arg__1: str, /, defaultValue: object = ..., type: object | None = ...
    ) -> object: ...

    @Slot(str, result="QVariant")
    @Slot(str, "QVariant", result="QVariant")
    @override
    def value(
        self,
        arg__1: str,
        /,
        defaultValue: object = _NULL,
        type: object | None = None,
    ) -> object:
        return super().value(
            arg__1,
            *((defaultValue,) if defaultValue is not self._NULL else ()),
            type=type,
        )

    @Slot(result="QStringList")
    @override
    def allKeys(self) -> list[str]:
        return super().allKeys()

    @Slot(result="QStringList")
    @override
    def childKeys(self) -> list[str]:
        return super().childKeys()

    @Slot(result="QStringList")
    @override
    def childGroups(self) -> list[str]:
        return super().childGroups()

    @Slot()
    @override
    def sync(self) -> None:
        super().sync()

    @Slot(result=str)
    @override
    def fileName(self) -> str:
        return super().fileName()

    @Slot(str, result=bool)
    @override
    def contains(self, key: str, /) -> bool:
        return super().contains(key)

    @Slot(str)
    @override
    def remove(self, key: str, /) -> None:
        super().push(self._Remove(super(QUndoStack, self), key))

    @override
    def beginGroup(self, prefix: str, /) -> NoReturn:
        raise NotImplementedError(self.tr("Settings.beginGroup() is not supported."))

    @override
    def endGroup(self) -> NoReturn:
        raise NotImplementedError(self.tr("Settings.endGroup() is not supported."))

    @override
    def push(self, cmd: QUndoCommand, /) -> NoReturn:
        raise NotImplementedError(self.tr("Settings.push() is not supported."))

    @override
    def beginReadArray(self, prefix: str, /) -> NoReturn:
        raise NotImplementedError(
            self.tr("Settings.beginReadArray() is not supported.")
        )

    @override
    def endArray(self) -> NoReturn:
        raise NotImplementedError(self.tr("Settings.endArray() is not supported."))

    @override
    def beginWriteArray(self, prefix: str, /, size: int | None = None) -> NoReturn:
        raise NotImplementedError(
            self.tr("Settings.beginWriteArray() is not supported.")
        )

    @overload
    def group(self, /) -> str: ...

    @overload
    def group(self, group: str, /) -> SettingsGroupView: ...

    @Slot(result=str)
    @Slot(str, result=QObject)
    @override
    def group(self, group: str | None = None, /) -> str | SettingsGroupView:
        if group is None:
            return super().group()
        else:
            return SettingsGroupView(self, group)

    @override
    def __iter__(self) -> Iterator[str]:
        yield from self.allKeys()

    @Slot(result=int)
    @override
    def __len__(self) -> int:
        return sum(1 for _ in self)

    @Slot(str, result="QVariant")
    @override
    def __getitem__(self, key: str, /) -> object:
        if not self.contains(key):
            raise KeyError(self.tr("{} is not in {}.").format(key, self.fileName()))
        return self.value(key)

    @Slot(str, "QVariant")
    @override
    def __setitem__(self, key: str, value: object, /) -> None:
        self.setValue(key, value)

    @Slot(str)
    @override
    def __delitem__(self, key: str, /) -> None:
        if not self.contains(key):
            raise KeyError(self.tr("{} is not in {}.").format(key, self.fileName()))
        self.remove(key)


class SettingsGroupView(QObject, MutableMapping[str, object], metaclass=QABCMeta):
    @override
    def __init__(
        self,
        settings: Settings | Self,
        group: str,
        /,
        parent: QObject | None = None,
        *,
        objectName: str | None = None,
    ) -> None:
        super().__init__(parent, objectName=objectName)
        self._settings: Settings | Self = settings
        self._group: str = group + "/"

    @override
    def __iter__(self) -> Iterator[str]:
        for key in self._settings:
            if key.startswith(self._group):
                yield key

    @Slot(result=int)
    @override
    def __len__(self) -> int:
        return sum(1 for _ in self)

    @Slot(str, result="QVariant")
    @override
    def __getitem__(self, key: str) -> object:
        return self._settings[self._group + key]

    @Slot(str, "QVariant")
    @override
    def __setitem__(self, key: str, value: object) -> None:
        self._settings[self._group + key] = value

    @Slot(str)
    @override
    def __delitem__(self, key: str) -> None:
        del self._settings[self._group + key]

    @Slot(str, result=QObject)
    def group(self, group: str, /) -> Self:
        return type(self)(self, group)
