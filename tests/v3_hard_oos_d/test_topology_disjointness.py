from training.v3_hard_oos_d.programs import topology_inventory, ABC_TOPOLOGIES

def test_hard_d_topologies_are_disjoint_from_abc_singleton_family():
    inv=topology_inventory()
    assert inv
    assert inv.isdisjoint(ABC_TOPOLOGIES)
