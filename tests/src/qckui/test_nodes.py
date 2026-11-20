from qckui.nodes import Nodes


def test_extensions(nodes: Nodes) -> None:
    nodes.reload("extensions.calc")
    assert nodes["calc.Add"].inputs["x"].annotation.__name__ == "Addable"
    assert nodes["calc.Sub"].outputs["result"] is object


def test_disk(nodes: Nodes) -> None:
    nodes.reload("test.calc")
    assert nodes["test.calc.Mul"].outputs["result"] is object
    assert (
        nodes["test.calc.truediv.Truediv"].inputs["x"].annotation.__name__
        == "Truedivable"
    )
