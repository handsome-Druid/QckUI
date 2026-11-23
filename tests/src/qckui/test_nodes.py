from qckui.nodes import Nodes


def test_extensions(nodes: Nodes) -> None:
    nodes.reload("calc")
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
        del nodes._nodes[key]  # pyright: ignore[reportPrivateUsage]
    assert not nodes
    nodes.reload("test")
    single_shot_id: int = id(nodes["test.test.singleshot.SingleShot"].cls)
    nodes.reload("test.test")
    assert id(nodes["test.test.singleshot.SingleShot"].cls) != single_shot_id
    mul_id: int = id(nodes["test.test.calc.Mul"].cls)
    div_id: int = id(nodes["test.test.calc.truediv.Truediv"].cls)
    nodes.reload("test.test.calc.truediv.Truediv")
    assert id(nodes["test.test.calc.truediv.Truediv"].cls) != div_id
    assert id(nodes["test.test.calc.Mul"].cls) == mul_id
