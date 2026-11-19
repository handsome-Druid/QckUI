from PySide6.QtCore import QObject, Slot

from qckui.model import Settings, SettingsGroupView


class Workflow(Settings):
    @property
    @Slot(result=QObject)
    def nodes(self) -> SettingsGroupView:
        return self.group("Nodes")

    @property
    @Slot(result=QObject)
    def sources(self) -> SettingsGroupView:
        return self.group("Sources")

    @Slot(str, str, str, str, result=bool)
    def canConnect(
        self, sourceNode: str, sourcePort: str, targetNode: str, targetPort: str
    ) -> bool:
        source_node: SettingsGroupView = self.nodes.group(sourceNode)
        target_node: SettingsGroupView = self.nodes.group(targetNode)
        return issubclass(
            getattr(NodeManager, cast(str, source_node["category"]))[
                source_node["module"]
            ][source_node["cls"]].outputs[sourcePort],
            getattr(NodeManager, cast(str, target_node["category"]))[
                target_node["module"]
            ][target_node["cls"]]
            .inputs[targetPort]
            .annotation,
        )
