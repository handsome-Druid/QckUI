from importlib.machinery import ModuleSpec
from importlib.util import module_from_spec
from pathlib import Path
from sys import modules

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
    nodes._test_dir = QDir(path=fixtures / "nodes")  # pyright: ignore[reportAttributeAccessIssue]
    nodes._categorys = (*nodes._categorys, "test")  # pyright: ignore[reportAttributeAccessIssue, reportPrivateUsage]
    spec = ModuleSpec(name="test", loader=None, is_package=True)
    spec.submodule_search_locations = [str(object=fixtures / "nodes")]
    modules["test"] = module_from_spec(spec)
    return nodes
