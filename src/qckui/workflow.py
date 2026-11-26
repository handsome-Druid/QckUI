from logging import Logger, getLogger
from typing import TYPE_CHECKING, cast

from PySide6.QtCore import QCoreApplication, QObject, Slot

from qckui.model import Settings, SettingsGroupView

if TYPE_CHECKING:
    from qckui.nodes import Nodes

_logger: Logger = getLogger(name=__name__)


class Workflow(Settings):
    @property
    @Slot(result=QObject)
    def nodes(self) -> SettingsGroupView:
        return self.group("Nodes")

    @property
    @Slot(result=QObject)
    def sources(self) -> SettingsGroupView:
        return self.group("Sources")

    @property
    def _nodes(self) -> Nodes:
        app: QCoreApplication | None = QCoreApplication.instance()
        assert app is not None
        return app.property("nodes")

    @Slot(str, str, str, str, result=bool)
    def canConnect(
        self, sourceNode: str, sourcePort: str, targetNode: str, targetPort: str
    ) -> bool:
        source_node: SettingsGroupView = self.nodes.group(sourceNode)
        target_node: SettingsGroupView = self.nodes.group(targetNode)
        try:
            return issubclass(
                self._nodes[cast(str, source_node["path"])].outputs[sourcePort],
                self._nodes[cast(str, target_node["path"])]
                .inputs[targetPort]
                .annotation,
            )
        except TypeError:
            _logger.exception(
                msg=self.tr(
                    f"Unable to detect if the connection is valid between {sourceNode}:{sourcePort} and {targetNode}:{targetPort}"
                )
            )
            return True
