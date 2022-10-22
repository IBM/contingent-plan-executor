from graphviz import Digraph


def test_graph():
    gra = Digraph()
    gra.node("a", "ACT1")
    gra.node("b", "act2")
    gra.node("c", "test")
    gra.edges(["ab", "ac"])
    gra

