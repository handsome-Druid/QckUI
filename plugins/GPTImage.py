from collections.abc import Iterable
from typing import Annotated, Literal, Protocol, override, runtime_checkable

from PySide6.QtCore import (
    QBuffer,
    QByteArray,
    QCoreApplication,
    QEventLoop,
    QIODevice,
    QJsonDocument,
    QMetaObject,
    QObject,
    Signal,
)
from PySide6.QtGui import QImage, QImageWriter
from PySide6.QtNetwork import (
    QHttpMultiPart,
    QHttpPart,
    QNetworkAccessManager,
    QNetworkReply,
    QNetworkRequest,
)

__all__: list[str] = ["GPTImage"]


class Progress:
    def __init__(self, msg: str, value: int, /) -> None:
        self._progress: tuple[str, int] = (msg, value)

    def progress(self) -> tuple[str, int]:
        return self._progress


class Result:
    def __init__(self, values: Iterable[QImage], /) -> None:
        self._values: Iterable[QImage] = values

    def images(self) -> Iterable[QImage]:
        return self._values


@runtime_checkable
class Images(Protocol):
    def images(self) -> Iterable[QImage]: ...


class GPTImage(QObject):
    error: Annotated[Signal, str] = Signal(object)
    images: Annotated[Signal, Result] = Signal(object)
    progress: Annotated[Signal, Progress] = Signal(object)

    @override
    def __init__(
        self, /, parent: QObject | None = None, *, objectName: str | None = None
    ) -> None:
        super().__init__(parent, objectName=objectName)
        self._replys: set[QNetworkReply] = set()

    def __call__(
        self,
        url: str,
        api_key: str,
        prompt: str,
        /,
        image: Images | None = None,
        *,
        n: Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10] | None = None,
        size: str | None = None,
        model: str | None = None,
    ) -> None:
        self.progress.emit(Progress(self.tr("Preparing request..."), 5))
        app: QCoreApplication | None = QCoreApplication.instance()
        assert app is not None
        request = QNetworkRequest(
            url + ("/v1/images/edits" if image else "/v1/images/generations")
        )
        request.setRawHeader(b"Authorization", b"Bearer %s" % api_key.encode())
        payload: dict[str, str | int] = {
            k: v
            for k, v in (
                ("prompt", prompt),
                ("n", n),
                ("size", size),
                ("model", model),
            )
            if v
        }
        if image:
            body: QHttpMultiPart | QByteArray = QHttpMultiPart(
                QHttpMultiPart.ContentType.FormDataType
            )
            for index, data in enumerate(image.images(), start=1):
                buffer = QBuffer()
                buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                writer = QImageWriter(buffer, b"PNG")
                if not writer.write(data):
                    raise ValueError(writer.errorString())
                part = QHttpPart()
                part.setHeader(
                    QNetworkRequest.KnownHeaders.ContentDispositionHeader,
                    f'form-data; name="image[]"; filename="image_{index}.png"',
                )
                part.setHeader(
                    QNetworkRequest.KnownHeaders.ContentTypeHeader,
                    "image/png",
                )
                part.setBody(buffer.data())
                body.append(part)
            for k, v in payload.items():
                part = QHttpPart()
                part.setHeader(
                    QNetworkRequest.KnownHeaders.ContentDispositionHeader,
                    f'form-data; name="{k}"',
                )
                part.setBody(str(object=v).encode())
                body.append(part)
        else:
            request.setHeader(
                QNetworkRequest.KnownHeaders.ContentTypeHeader,
                "application/json",
            )
            body = QJsonDocument.fromVariant(payload).toJson()
        if not hasattr(self, "_manager"):
            manager = app.property("qNetworkAccessManager")
            if (
                isinstance(manager, QNetworkAccessManager)
                and manager.thread().isCurrentThread()
            ):
                self._manager: QNetworkAccessManager = manager
            else:
                self._manager = QNetworkAccessManager(parent=self)
        reply: QNetworkReply = self._manager.post(request, body)
        self._replys.add(reply)
        if isinstance(body, QHttpMultiPart):
            body.setParent(reply)
        reply.finished.connect(
            lambda reply=reply: (
                self._replys.discard(reply),
                self._on_finished(reply),
            ),
        )
        self.progress.emit(Progress(self.tr("Waiting for response..."), 30))

    def _on_finished(self, reply: QNetworkReply, /) -> None:
        try:
            self.progress.emit(Progress(self.tr("Parsing response..."), 80))
            if reply.error() != QNetworkReply.NetworkError.NoError:
                self.error.emit(
                    reply.errorString() + "\n" + bytes(reply.readAll().data()).decode(),
                )
                return
            images: list[QImage] = []
            replys: set[QNetworkReply] = set()
            loop = QEventLoop(parent=self)
            for data in QJsonDocument.fromJson(reply.readAll()).toVariant()["data"]:
                if "b64_json" in data:
                    images.append(
                        QImage.fromData(
                            QByteArray.fromBase64(data["b64_json"].encode())
                        )
                    )
                elif "url" in data:
                    reply_: QNetworkReply = self._manager.get(
                        QNetworkRequest(data["url"])
                    )
                    replys.add(reply_)
                    reply_.finished.connect(
                        lambda reply=reply_: (
                            images.append(QImage.fromData(reply.readAll()))
                            if reply.error() == QNetworkReply.NetworkError.NoError
                            else self.error.emit(
                                reply.errorString()
                                + "\n"
                                + bytes(reply.readAll().data()).decode(),
                            ),
                            replys.discard(reply),
                            (self.images.emit(Result(images)), loop.quit())
                            if not replys
                            else None,
                        )
                    )
                if replys:
                    self.progress.emit(Progress(self.tr("Downloading images"), 80))
                    loop.exec()
                else:
                    loop.deleteLater()
                    self.images.emit(Result(images))
            self.progress.emit(Progress(self.tr("Task finished"), 100))
        finally:
            reply.deleteLater()

    @override
    def deleteLater(self) -> None:
        for reply in self._replys:
            QMetaObject.invokeMethod(reply, "abort")
            reply.deleteLater()
        super().deleteLater()
