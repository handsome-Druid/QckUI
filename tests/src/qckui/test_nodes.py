from qckui.nodes import Nodes


def test_extensions(nodes: Nodes) -> None:
    nodes.reload("extensions.calc")
    assert nodes["calc.Add"].inputs["x"].annotation.__name__ == "Addable"
    assert nodes["calc.Sub"].outputs["result"] is object


def test_disk(nodes: Nodes) -> None:
    nodes.reload("test.test.calc")
    assert nodes["test.test.calc.Mul"].outputs["result"] is object
    assert (
        nodes["test.test.calc.truediv.Truediv"].inputs["x"].annotation.__name__
        == "Truedivable"
    )


def test_reload(nodes: Nodes) -> None:
    for key in tuple(nodes):
        if key.startswith("test.test.calc"):
            nodes._nodes.pop(key)  # pyright: ignore[reportPrivateUsage]
    nodes.reload("test.test")
    assert nodes["test.test.calc.truediv.Truediv"]
    assert nodes["test.test.calc.Mul"]
    mul_id: int = id(nodes["test.test.calc.Mul"].cls)
    div_id: int = id(nodes["test.test.calc.truediv.Truediv"].cls)
    nodes.reload("test.test.calc.truediv")
    assert id(nodes["test.test.calc.truediv.Truediv"].cls) != div_id
    assert id(nodes["test.test.calc.Mul"].cls) == mul_id
