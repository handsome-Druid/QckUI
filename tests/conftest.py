from pathlib import Path

from PySide6.QtGui import QGuiApplication
from pytest import fixture

from qckui.nodes import Nodes, QDir


@fixture(scope="session")
def qapp_cls() -> type[QGuiApplication]:
    return QGuiApplication


@fixture(scope="session")
def fixtures() -> Path:
    return Path(__file__).parent / "fixtures"


@fixture(scope="session")
def nodes(qapp: QGuiApplication, fixtures: Path) -> Nodes:
    nodes = Nodes(parent=qapp)
    nodes._dir["test"] = QDir(path=fixtures / "nodes")  # pyright: ignore[reportPrivateUsage]
    return nodes
