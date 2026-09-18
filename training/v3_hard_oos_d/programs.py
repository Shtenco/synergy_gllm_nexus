from .ast import AstNode,NodeKind,topology_fingerprint

def A(x): return AstNode.atom(x)
def AND(*xs): return AstNode(NodeKind.AND,tuple(xs),arity=len(xs))
def I(a,b): return AstNode(NodeKind.IMPLIES,(a,b),arity=2)

def program_templates():
    return (
        I(AND(A('a'),A('b')),A('c')),
        I(AND(A('a'),A('b'),A('c')),A('d')),
        I(AND(A('a'),AstNode(NodeKind.STATE_GATE,(A('s'),)),AstNode(NodeKind.INHIBITOR,(A('i'),))),A('c')),
        I(AND(A('a'),AstNode(NodeKind.TEMPORAL_AFTER,(A('t'),))),A('b')),
        I(AND(A('a'),A('b')),AstNode(NodeKind.INHIBITOR,(A('c'),))),
        I(AND(A('a'),AstNode(NodeKind.EXCEPTION,(A('e'),))),A('b')),
        I(AND(A('a'),A('b')),AstNode(NodeKind.COMPOSE,(A('c'),A('d')))),
        AstNode(NodeKind.COUNTERFACTUAL_INTERVENTION,(I(AND(A('a'),A('b')),A('c')),)),
    )
ABC_TOPOLOGIES={topology_fingerprint(A('x')),topology_fingerprint(AstNode(NodeKind.SYMMETRIC,(A('x'),))),topology_fingerprint(AstNode(NodeKind.INVERSE,(A('x'),))),topology_fingerprint(AstNode(NodeKind.INHIBITOR,(A('x'),)))}
def topology_inventory(): return {topology_fingerprint(x) for x in program_templates()}
