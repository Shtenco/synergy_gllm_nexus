from training.v3_hard_oos_d.ast import AstNode, NodeKind, topology_fingerprint

def test_rename_preserves_topology_but_nesting_changes_it():
    a=AstNode(NodeKind.IMPLIES,(AstNode(NodeKind.AND,(AstNode.atom('op:a'),AstNode.atom('op:b'))),AstNode.atom('op:c')))
    b=AstNode(NodeKind.IMPLIES,(AstNode(NodeKind.AND,(AstNode.atom('x'),AstNode.atom('y'))),AstNode.atom('z')))
    c=AstNode(NodeKind.IMPLIES,(AstNode(NodeKind.AND,(AstNode.atom('x'),AstNode(NodeKind.NOT,(AstNode.atom('y'),)))),AstNode.atom('z')))
    assert topology_fingerprint(a)==topology_fingerprint(b)
    assert topology_fingerprint(a)!=topology_fingerprint(c)
